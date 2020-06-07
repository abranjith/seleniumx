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
import errno
import warnings
import asyncio
from asyncio.subprocess import PIPE

from seleniumx.common.exceptions import WebDriverException
from seleniumx.webdriver.common.utils import NetworkUtils, HttpUtils

try:
    from asyncio.subprocess import DEVNULL
    _HAS_NATIVE_DEVNULL = True
except ImportError:
    DEVNULL = -3
    _HAS_NATIVE_DEVNULL = False

LOCALHOST = "localhost"

class Service(object):

    def __init__(
        self,
        executable : str,
        port : int = 0,
        log_file : int = DEVNULL,
        env : dict = None,
        start_error_message : str = ""
    ):
        self.path = executable
        self.port = port
        self._service_url = None

        if not _HAS_NATIVE_DEVNULL and log_file == DEVNULL:
            #ignores anything directed to this
            log_file = open(os.devnull, "wb")
        
        self.start_error_message = start_error_message
        self.log_file = log_file
        self.env = env or os.environ

    @property
    def service_url(self):
        """ Gets the url of the Service """
        self._service_url = HttpUtils.get_url(LOCALHOST, "", port=self.port)
        return self._service_url
    
    @service_url.setter
    def service_url(self, url):
        if url is not None:
            self._service_url = url
    
    async def __aenter__(self):
        return self

    async def __aexit__(self, *excinfo):
        await self.stop()

    def command_line_args(self):
        raise NotImplementedError("This method needs to be implemented in a sub class")

    async def start(self):
        """ Starts the WebDriver Service (Server)

        :Exceptions:
         - WebDriverException : Raised either when it can't start the service
           or when it can't connect to the service
        """
        path = os.path.basename(self.path)
        message = self.start_error_message
        try:
            if self.port == 0:
                self.port = await NetworkUtils.free_port()
            cmd = self.command_line_args()
            self.process = await asyncio.create_subprocess_exec(self.path, *cmd, env=self.env,
                                            close_fds=platform.system() != "Windows",
                                            stdout=self.log_file,
                                            stderr=self.log_file,
                                            stdin=PIPE)
        except TypeError:
            raise
        except OSError as err:
            if err.errno == errno.ENOENT:
                raise WebDriverException(f"'{path}' executable needs to be in PATH. {message}")
            elif err.errno == errno.EACCES:
                raise WebDriverException(f"'{path}' executable may have wrong permissions. {message}")
            else:
                raise
        except Exception as e:
            raise WebDriverException(f"The executable '{path}' needs to be available in the path. {message}{os.linesep}{str(e)}")
        
        for _ in range(30):
            self.assert_process_still_running()
            if await self.is_connectable():
                break
            else:
                await asyncio.sleep(1)
        else:
            raise WebDriverException(f"Cannot connect to the Service {self.path}")   
    
    async def send_remote_shutdown_command(self):
        #send shutdown signal to WebDriver
        try:
            await HttpUtils.get(f"{self.service_url}/shutdown")
        except Exception:
            return

        #wait for shutdown upto 30 seconds
        for _ in range(30):
            if not await self.is_connectable():
                break
            else:
                await asyncio.sleep(1)
        else:
            warnings.warn(f"{self.service_url} is still connectable even after 30 seconds of issuing shutdown. \
                            Please check if the WebDriver is still running")

    async def stop(self):
        """ Stops the WebDriver Service (Server) """
        if self.log_file != PIPE and not (self.log_file == DEVNULL and _HAS_NATIVE_DEVNULL):
            try:
                self.log_file.close()
            except Exception:
                pass

        if self.process is None:
            return

        try:
            await self.send_remote_shutdown_command()
        except Exception as ex:
            warnings.warn(f"Something went wrong shutting down {self.service_url}. Please check if the WebDriver is still running. \
                        Details - {str(ex)}")

        try:
            if self.process:
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
    
    async def is_connectable(self):
        return await HttpUtils.is_url_connectable(self.port)
    
    def assert_process_still_running(self):
        """ Check is process is still running by validating the return code"""
        return_code = self.process.returncode
        if return_code is not None:
            raise WebDriverException(f"Service {self.path} unexpectedly exited. Status code was: {return_code}")
