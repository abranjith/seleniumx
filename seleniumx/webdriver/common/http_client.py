import asyncio
import httpx
from seleniumx.webdriver.common.enums import HttpMethod

#TODO - these singleton instances might not  work in all cases. Might need a design where instance is spinned up based on input args
class _BaseClient(object):
    # NOTE - soft_limit is for max keep alives and hard_limit for connection pool max number limit
    KEEPALIVE_POOL_LIMIT = httpx.PoolLimits(soft_limit=10, hard_limit=10)
    NOKEEPALIVE_POOL_LIMIT = httpx.PoolLimits(soft_limit=0, hard_limit=10)
    DEFAULT_TIMEOUT = httpx.Timeout(60.0, connect_timeout=60.0)

class HttpClient(_BaseClient):
    """ Wrapper for making async http calls"""

    def __init__(
        self,
        base_url = None,
        keep_alive = True,
        timeout = None,
        cert = None,
        headers = None,
        verify = True
    ):
        self._common_headers = headers
        self._base_url = base_url
        pool_limits = HttpClient.KEEPALIVE_POOL_LIMIT if keep_alive else HttpClient.NOKEEPALIVE_POOL_LIMIT
        timeout = HttpClient.DEFAULT_TIMEOUT if timeout is None else httpx.Timeout(60.0, connect_timeout=timeout)
        self._client = httpx.AsyncClient(base_url=base_url, headers=headers, timeout=timeout, pool_limits=pool_limits, cert=cert, verify=verify)
    
    @property
    def base_url(self):
        if self._client:
            url = self._client.base_url
            if isinstance(url, httpx.URL):
                return str(url)
            return url
    
    @base_url.setter
    def base_url(self, url):
        if url is not None:
            self._client.base_url = httpx.URL(url)
    
    async def get(
        self,
        url,
        params = None,
        headers = None,
        timeout = None
    ):
        response = await self._client.get(url, params=params, headers=headers, timeout=timeout)
        return response
    
    async def post(
        self,
        url,
        payload,
        params = None,
        headers = None,
        timeout = None
    ):
        response = await self._client.post(url, params=params, json=payload, headers=headers, timeout=timeout)
        return response
    
    async def delete(
        self,
        url,
        params = None,
        headers = None,
        timeout = None
    ):
        response = await self._client.delete(url, params=params, headers=headers, timeout=timeout)
        return response
    
    async def request(
        self,
        http_method : HttpMethod,
        url,
        params = None,
        headers = None,
        payload = None,
        timeout = None
    ):
        response = None
        if http_method == HttpMethod.GET:
            response = await self.get(url, params=params, headers=headers, timeout=timeout)
        elif http_method == HttpMethod.POST:
            response = await self.post(url, payload, params=params, headers=headers, timeout=timeout)
        elif http_method == HttpMethod.DELETE:
            response = await self.delete(url, params=params, headers=headers, timeout=timeout)
        else:
            raise ValueError(f"{http_method} is not supported currently. Please speak to maintainer in case this is an error")
        return response
    
    #closes underlying connection pool
    async def close(self):
        if self._client and hasattr(self._client, "aclose"):
            await self._client.aclose()
            self._client = None
    
    def _merge_url(self, relative_url):
        u = None
        if self._base_url is None:
            u = httpx.URL("", allow_relative=True)
        else:
            u = httpx.URL(self._base_url)
        u.join(relative_url)
        return u
    
    def _merge_header(self, headers):
        h = self._common_headers or {}
        if headers:
            h.update(headers)
        return h