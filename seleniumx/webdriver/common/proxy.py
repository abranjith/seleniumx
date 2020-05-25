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

from enum import Enum

#TODO - not sure why this conversion is needed. Dont see this in java bindings
class ProxyTypeFactory(object):
    """ Factory for proxy types. """

    @staticmethod
    def make(ff_value, string):
        return {'ff_value': ff_value, 'string': string}


class ProxyType(Enum):
    """ Set of possible types of proxy.

    #NOTE - Keep these in sync with the Firefox preferences numbers:
            http://kb.mozillazine.org/Network.proxy.type
    """
    
    DIRECT = "DIRECT"             # Direct connection, no proxy (default on Windows)
    MANUAL = "MANUAL"             # Manual proxy settings (e.g. for httpProxy)
    PAC = "PAC"                   # Proxy auto-configuration from URL

    RESERVED_1 = "RESERVED_1"     # Never used (but reserved in Firefox)

    AUTODETECT = "AUTODETECT"     # Proxy auto-detection (presumably with WPAD)
    SYSTEM = "SYSTEM"             # Use system settings (default on Linux)

    UNSPECIFIED = "UNSPECIFIED"

    @staticmethod
    def get_proxy_type_for_string(text):
        if not text:
            return ProxyType.UNSPECIFIED
        text = text.strip().upper()
        value = ProxyType.__members__.get(text)
        return value if value else ProxyType.UNSPECIFIED
    
    #string compare with name
    def __eq__(self, other):
        if isinstance(other, str):
            if str(self.name).upper() == other.strip().upper():
                return True
            return False
        return super().__eq__(other)
    
    def __ne__(self, other):
        return not self.__eq__(other)

class Proxy(object):
    """ Proxy contains information about proxy type and necessary proxy settings. """

    def __init__(self, raw=None):
        """ Creates a new Proxy.

        :Args:
         - raw: raw proxy data. If None, default values are used.
        """
        self.init_defaults()
        self.load_from_dict(raw)
    
    def init_defaults(self):
        self._proxy_type = ProxyType.UNSPECIFIED
        self._auto_detect = False
        self._ftp_proxy = None
        self._http_proxy = None
        self._no_proxy = None
        self._proxy_autoconfig_url = None
        self._ssl_proxy = None
        self._socks_proxy = None
        self._socks_username = None
        self._socks_password = None
        self._socks_version = None
    
    def load_from_dict(self, raw):
        if not (raw and isinstance(raw, dict)):
            return
        if raw.get('proxyType') is not None:
            self.proxy_type = ProxyType.get_proxy_type_for_string(raw['proxyType'])
        if raw.get('ftpProxy') is not None:
            self.ftp_proxy = raw['ftpProxy']
        if raw.get('httpProxy') is not None:
            self.http_proxy = raw['httpProxy']
        if raw.get('noProxy') is not None:
            self.no_proxy = raw['noProxy']
        if raw.get('proxyAutoconfigUrl') is not None:
            self.proxy_autoconfig_url = raw['proxyAutoconfigUrl']
        if raw.get('sslProxy') is not None:
            self.sslProxy = raw['sslProxy']
        if raw.get('autodetect') is not None:
            self.auto_detect = raw['autodetect']
        if raw.get('socksProxy') is not None:
            self.socks_proxy = raw['socksProxy']
        if raw.get('socksUsername') is not None:
            self.socks_username = raw['socksUsername']
        if raw.get('socksPassword') is not None:
            self.socks_password = raw['socksPassword']
        if raw.get('socksVersion') is not None:
            self.socks_version = raw['socksVersion']
    
    @staticmethod
    def from_capabilities(capabilities):
        """
        Extracts proxy information as capability in specified capabilities.

        :Args:
         - capabilities: The capabilities to which proxy will be added.
        """
        if not (capabilities and isinstance(capabilities, dict)):
            return Proxy()
        proxy = capabilities.get('proxy')
        if isinstance(proxy, Proxy):
            return proxy
        if isinstance(proxy, dict):
            return Proxy(raw=proxy)
        return Proxy()

    @property
    def proxy_type(self):
        """
        Returns proxy type as `ProxyType`.
        """
        return self._proxy_type

    @proxy_type.setter
    def proxy_type(self, value):
        """
        Sets proxy type.

        :Args:
         - value: The proxy type.
        """
        self._verify_proxy_type_compatibility(value)
        self._proxy_type = value

    @property
    def auto_detect(self):
        """
        Returns autodetect setting.
        """
        return self._auto_detect

    @auto_detect.setter
    def auto_detect(self, value):
        """
        Sets autodetect setting.

        :Args:
         - value: The autodetect value.
        """
        if not isinstance(value, bool):
            raise ValueError("Autodetect proxy value needs to be a boolean")

        if self._auto_detect is not value:
            self.proxy_type = ProxyType.AUTODETECT
            self._auto_detect = value

    @property
    def ftp_proxy(self):
        """
        Returns ftp proxy setting.
        """
        return self._ftp_proxy

    @ftp_proxy.setter
    def ftp_proxy(self, value):
        """
        Sets ftp proxy setting.

        :Args:
         - value: The ftp proxy value.
        """
        self.proxy_type = ProxyType.MANUAL
        self._ftp_proxy = value

    @property
    def http_proxy(self):
        """
        Returns http proxy setting.
        """
        return self._http_proxy

    @http_proxy.setter
    def http_proxy(self, value):
        """
        Sets http proxy setting.

        :Args:
         - value: The http proxy value.
        """
        self.proxy_type = ProxyType.MANUAL
        self._http_proxy = value

    @property
    def no_proxy(self):
        """
        Returns noproxy setting.
        """
        return self._no_proxy

    @no_proxy.setter
    def no_proxy(self, value):
        """
        Sets noproxy setting.

        :Args:
         - value: The noproxy value.
        """
        self.proxy_type = ProxyType.MANUAL
        if isinstance(value, (list, tuple)):
            value = ", ".join(value)
        self._no_proxy = value

    @property
    def proxy_autoconfig_url(self):
        """
        Returns proxy autoconfig url setting.
        """
        return self._proxy_autoconfig_url

    @proxy_autoconfig_url.setter
    def proxy_autoconfig_url(self, value):
        """
        Sets proxy autoconfig url setting.

        :Args:
         - value: The proxy autoconfig url value.
        """
        self.proxy_type = ProxyType.PAC
        self._proxy_autoconfig_url = value

    @property
    def ssl_proxy(self):
        """
        Returns https proxy setting.
        """
        return self._ssl_proxy

    @ssl_proxy.setter
    def ssl_proxy(self, value):
        """
        Sets https proxy setting.

        :Args:
         - value: The https proxy value.
        """
        self.proxy_type = ProxyType.MANUAL
        self._ssl_proxy = value

    @property
    def socks_proxy(self):
        """
        Returns socks proxy setting.
        """
        return self._socks_proxy

    @socks_proxy.setter
    def socks_proxy(self, value):
        """
        Sets socks proxy setting.

        :Args:
         - value: The socks proxy value.
        """
        self.proxy_type = ProxyType.MANUAL
        self._socks_proxy = value

    @property
    def socks_username(self):
        """
        Returns socks proxy username setting.
        """
        return self._socks_username

    @socks_username.setter
    def socks_username(self, value):
        """
        Sets socks proxy username setting.

        :Args:
         - value: The socks proxy username value.
        """
        self.proxy_type = ProxyType.MANUAL
        self._socks_username = value

    @property
    def socks_password(self):
        """
        Returns socks proxy password setting.
        """
        return self._socks_password

    @socks_password.setter
    def socks_password(self, value):
        """
        Sets socks proxy password setting.

        :Args:
         - value: The socks proxy password value.
        """
        self.proxy_type = ProxyType.MANUAL
        self._socks_password = value

    @property
    def socks_version(self):
        """
        Returns socks proxy version setting.
        """
        return self._socks_version

    @socks_version.setter
    def socks_version(self, value):
        """
        Sets socks proxy version setting.

        :Args:
         - value: The socks proxy version value.
        """
        self.proxy_type = ProxyType.MANUAL
        if str(value).isnumeric():
            value = int(value)
        self._socks_version = value

    def _verify_proxy_type_compatibility(self, compatible_proxy):
        if self._proxy_type != ProxyType.UNSPECIFIED and self._proxy_type != compatible_proxy:
            raise Exception(f"Specified proxy type ({compatible_proxy.value}) not compatible with current setting ({self._proxy_type.value})")
    
    def add_to_capabilities(self, capabilities):
        """
        Adds proxy information as capability in specified capabilities.

        :Args:
         - capabilities: The capabilities to which proxy will be added.
        """
        proxy_caps = self.to_json()
        capabilities['proxy'] = proxy_caps
    
    def to_json(self):
        proxy_caps = {}
        proxy_caps['proxyType'] = self.proxy_type.value
        if self.auto_detect:
            proxy_caps['autodetect'] = self.auto_detect
        if self.ftp_proxy:
            proxy_caps['ftpProxy'] = self.ftp_proxy
        if self.http_proxy:
            proxy_caps['httpProxy'] = self.http_proxy
        if self.proxy_autoconfig_url:
            proxy_caps['proxyAutoconfigUrl'] = self.proxy_autoconfig_url
        if self.ssl_proxy:
            proxy_caps['sslProxy'] = self.ssl_proxy
        if self.no_proxy:
            proxy_caps['noProxy'] = self.no_proxy
        if self.socks_proxy:
            proxy_caps['socksProxy'] = self.socks_proxy
        if self.socks_username:
            proxy_caps['socksUsername'] = self.socks_username
        if self.socks_password:
            proxy_caps['socksPassword'] = self.socks_password
        if self.socks_version:
            proxy_caps['socksVersion'] = self.socks_version
        return proxy_caps
    
    to_dict = to_json

    def __str__(self):
        s = "Proxy("
        if (self.proxy_type in [ProxyType.AUTODETECT, ProxyType.DIRECT, ProxyType.MANUAL, ProxyType.SYSTEM]):
            s += self.proxy_type.value.lower()
        elif (self.proxy_type == ProxyType.PAC):
            s += f"pac: {self.proxy_autoconfig_url}"
        if self.ftp_proxy:
            s += f", ftp={self.ftp_proxy}"
        if self.http_proxy:
            s += f", http={self.http_proxy}"
        if self.socks_proxy:
            s += f", socks={self.socks_proxy}"
        if self.ssl_proxy:
            s += f", ssl={self.ssl_proxy}"
        s += ")"
        return s
    
    __repr__ = __str__