# Licensed to the Software Freedom Conservancy (SFC) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The SFC licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.


import os
import platform
import time
import shlex
import shutil
import warnings
import asyncio
from asyncio.subprocess import PIPE
from seleniumx.common.exceptions import WebDriverException
from seleniumx.webdriver.common.utils import HttpUtils, Platform

try:
    from asyncio.subprocess import DEVNULL
    _HAS_NATIVE_DEVNULL = True
except ImportError:
    DEVNULL = -3
    _HAS_NATIVE_DEVNULL = False

class FirefoxBinary(object):

    NO_FOCUS_LIBRARY_NAME = "x_ignore_nofocus.so"

    def __init__(
        self,
        firefox_path : str = None,
        log_file : int = DEVNULL
    ):
        """ Creates a new instance of Firefox binary.

        :Args:
         - firefox_path - Path to the Firefox executable. By default, it will be detected from the standard locations.
         - log_file - A file object to redirect the firefox process output to. It can be sys.stdout.
                      Please note that with parallel run the output won't be synchronous.
                      By default, it will be redirected to /dev/null.
        """
        self._start_cmd = firefox_path or self._get_firefox_start_cmd() or ""
        # We used to default to subprocess.PIPE instead of /dev/null, but after
        # a while the pipe would fill up and Firefox would freeze.
        if not _HAS_NATIVE_DEVNULL and log_file == DEVNULL:
            #ignores anything directed to this
            log_file = open(os.devnull, "wb")
        self._log_file = log_file or open(os.devnull, "wb")
        self.command_line = None
        
        self._ensure_path()
        # Rather than modifying the environment of the calling Python process
        # copy it and modify as needed.
        self._firefox_env = os.environ.copy()
        self._firefox_env["MOZ_CRASHREPORTER_DISABLE"] = "1"
        self._firefox_env["MOZ_NO_REMOTE"] = "1"
        self._firefox_env["NO_EM_RESTART"] = "1"
    
    def _ensure_path(self):
        if not self._start_cmd.strip():
            raise WebDriverException(
                f"""Failed to find firefox binary. You can set it by specifying the path to 'firefox_binary':

                from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
                binary = FirefoxBinary('/path/to/binary')
                driver = webdriver.Firefox(firefox_binary=binary)
                """)

    def add_command_line_options(self, *args):
        self.command_line = args

    async def launch_browser(self, profile, timeout = 30):
        """ Launches the browser for the given profile name. It is assumed the profile already exists. """
        self.profile = profile
        await self._start_from_profile_path(self.profile.path)
        await self._wait_until_connectable(timeout = timeout)
    
    async def _start_from_profile_path(self, path):
        self._firefox_env["XRE_PROFILE_PATH"] = path

        if Platform.is_linux():
            self._modify_link_library_path()
        command = ["-foreground"]
        if self.command_line is not None:
            for cli in self.command_line:
                command.append(cli)
        self.process = await asyncio.create_subprocess_exec(self._start_cmd, *command, env=self._firefox_env,
                                            close_fds = not Platform.is_windows(),
                                            stdout = self.log_file,
                                            stderr = self.log_file)

    async def _wait_until_connectable(self, timeout = 30):
        """ Blocks until the extension is connectable in the firefox. """
        timeout = int(timeout)
        for _ in range(timeout):
            self.assert_process_still_running()
            if await self.is_connectable():
                break
            else:
                await asyncio.sleep(1)
        else:
            await self.kill()
            raise WebDriverException(f"""Cannot connect to the service {self._start_cmd}. Possible firefox version mismatch.
                 You must use GeckoDriver instead for Firefox 48+.{os.linesep}Profile Dir - {self.profile.path}.{os.linesep}If you specified a log_file in the
                 FirefoxBinary constructor, check the same for details""")
    
    async def kill(self):
        """ Kill the browser. This is useful when the browser is stuck. """
        if self.log_file != PIPE and not (self.log_file == DEVNULL and _HAS_NATIVE_DEVNULL):
            try:
                self.log_file.close()
            except Exception:
                pass

        if self.process is None:
            return

        try:
            for stream in [self.process.stdin, self.process.stdout, self.process.stderr]:
                try:
                    stream.close()
                except AttributeError:
                    pass
            self.process.terminate()
            await self.process.wait()
            self.process.kill()
            self.process = None
        except OSError:
            pass

    def _get_firefox_start_cmd(self):
        """ Return the command to start firefox."""
        start_cmd = ""
        if Platform.is_mac():
            start_cmd = self._default_macos_location()
            # fallback to homebrew installation for mac users
            if not os.path.exists(start_cmd):
                start_cmd = os.path.expanduser("~") + start_cmd
        elif Platform.is_windows():
            start_cmd = self._find_exe_in_registry() or self._default_windows_location()
        else:
            for ffname in ["firefox", "iceweasel"]:
                start_cmd = self.which(ffname)
                if start_cmd is not None:
                    break
            else:
                # couldn't find firefox on the system path
                raise RuntimeError("Could not find firefox in your system PATH. Please specify the firefox binary location or install firefox")
        return start_cmd
    
    def _find_exe_in_registry(self):
        try:
            from winreg import OpenKey, QueryValue, HKEY_LOCAL_MACHINE, HKEY_CURRENT_USER
        except ImportError:
            warnings.warn("Could not find winreg module to read from windows registry")
        
        keys = [r"SOFTWARE\Classes\FirefoxHTML\shell\open\command",
                r"SOFTWARE\Classes\Applications\firefox.exe\shell\open\command"]
        command = ""
        for path in keys:
            try:
                key = OpenKey(HKEY_LOCAL_MACHINE, path)
                command = QueryValue(key, "")
                break
            except OSError:
                try:
                    key = OpenKey(HKEY_CURRENT_USER, path)
                    command = QueryValue(key, "")
                    break
                except OSError:
                    pass
        if not command:
            return ""
        return shlex.split(command)[0]
    
    def _default_macos_location(self):
        path = "/Applications/Firefox.app/Contents/MacOS/firefox-bin"
        return path

    def _default_windows_location(self):
        program_files = [os.getenv("PROGRAMFILES", r"C:\Program Files"),
                         os.getenv("PROGRAMFILES(X86)", r"C:\Program Files (x86)")]
        for path in program_files:
            binary_path = os.path.join(path, r"Mozilla Firefox\firefox.exe")
            if os.access(binary_path, os.X_OK):
                return binary_path
        return ""

    def _modify_link_library_path(self):
        existing_ld_lib_path = os.environ.get('LD_LIBRARY_PATH', "")
        new_ld_lib_path = self._extract_and_check(self.profile, "x86", "amd64")
        new_ld_lib_path += existing_ld_lib_path
        self._firefox_env["LD_LIBRARY_PATH"] = new_ld_lib_path
        self._firefox_env['LD_PRELOAD'] = self.NO_FOCUS_LIBRARY_NAME

    def _extract_and_check(self, profile, x86, amd64):
        paths = [x86, amd64]
        built_path = ""
        for path in paths:
            library_path = os.path.join(profile.path, path)
            if not os.path.exists(library_path):
                os.makedirs(library_path)
            shutil.copy(
                os.path.join(os.path.dirname(__file__), path, self.NO_FOCUS_LIBRARY_NAME),
                library_path)
            built_path += library_path + ":"
        return built_path

    def which(self, fname):
        """ Returns the fully qualified path by searching Path of the given name """
        for pt in os.environ['PATH'].split(os.pathsep):
            checkname = os.path.join(pt, fname)
            if os.access(checkname, os.X_OK) and not os.path.isdir(checkname):
                return checkname
        return None
    
    async def is_connectable(self):
        return await HttpUtils.is_url_connectable(self.profile.port)
    
    def assert_process_still_running(self):
        """ Check is process is still running by validating the return code"""
        return_code = self.process.returncode
        if return_code is not None:
            raise WebDriverException(f"""Service {self._start_cmd} unexpectedly exited. Status code was: {return_code}{os.linesep}
                If you specified a log_file in the FirefoxBinary constructor, check the same for details.""")
