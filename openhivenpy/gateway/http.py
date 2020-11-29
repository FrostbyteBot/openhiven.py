import aiohttp
import asyncio
import logging
import sys
import time
import json as json_decoder
from typing import Optional

import openhivenpy.exceptions as errs

__all__ = ('HTTPClient')


logger = logging.getLogger(__name__)

request_url_format = "https://{0}/{1}"

class HTTPClient():
    """`openhivenpy.gateway`
    
    HTTPClient
    ~~~~~~~~~~
    
    HTTPClient for requests and interaction with the Hiven API
    
    Parameter:
    ----------
    
    api_url: `str` - Url for the API which will be used to interact with Hiven. Defaults to 'https://api.hiven.io/v1' 
    
    host: `str` - Host URL. Defaults to "api.hiven.io"
    
    api_version: `str` - Version string for the API Version. Defaults to 'v1' 
    
    token: `str` - Needed for the authorization to Hiven.
    
    event_loop: `asyncio.AbstractEventLoop` - Event loop that will be used to execute all async functions.
    
    """
    def __init__(self, loop: Optional[asyncio.AbstractEventLoop] = asyncio.get_event_loop(), **kwargs):
        
        self._TOKEN = kwargs.get('token')
        self.host = kwargs.get('api_url', "api.hiven.io")
        self.api_version = kwargs.get('api_version', "v1")
        self.api_url = request_url_format.format(self.host, self.api_version)        
        
        self.headers = {"Authorization": self._TOKEN,
                        "Host": self.host}
        
        self.http_ready = False
        
        self.session = None
        self.loop = loop    
        
    async def connect(self) -> dict:
        """`openhivenpy.gateway.HTTPClient.connect()`

        Establishes for the HTTPClient a connection to Hiven
        
        """
        try:
            async def on_request_start(session, trace_config_ctx, params):
                logger.debug(f" [HTTP] >> Request with HTTP {params.method} started at {time.time()}")
                logger.debug(f" [HTTP] >> URL >> {params.url}")
         
            async def on_request_end(session, trace_config_ctx, params):
                logger.debug(f" [HTTP] << Request with HTTP {params.method} finished!")
                logger.debug(f" [HTTP] << Header << {params.headers}")
                logger.debug(f" [HTTP] << URL << {params.url}")
                logger.debug(f" [HTTP] << Response << {params.response}")
            
            async def on_request_exception(session, trace_config_ctx, params):
                logger.debug(f" [HTTP] << An exception occured while executing the request")
            
            async def on_request_redirect(session, trace_config_ctx, params):
                logger.debug(f" [HTTP] << REDIRECTING with URL {params.url} and HTTP {params.method}")
            
            async def on_connection_queued_start(session, trace_config_ctx, params):
                logger.debug(f" [HTTP] >> HTTP {params.method} with {params.url} queued!")
            
            trace_config = aiohttp.TraceConfig()
            trace_config.on_request_start.append(on_request_start)
            trace_config.on_request_end.append(on_request_end)
            trace_config.on_request_exception.append(on_request_exception)
            trace_config.on_request_redirect.append(on_request_redirect)
            trace_config.on_connection_queued_start.append(on_connection_queued_start)
            
            self.session = aiohttp.ClientSession(
                                                loop=self.loop,
                                                trace_configs=[trace_config])
            self.http_ready = True
            resp = await self.request("/users/@me", timeout=10)
            return resp
        
        except Exception as e:
            self.http_ready = False
            await self.session.close()
            logger.error(f" FAILED to create Session! Cause of Error: {sys.exc_info()[1].__class__.__name__}, {str(e)}")
            raise errs.UnableToCreateSession(f"FAILED to create Session!! Cause of Error: {sys.exc_info()[1].__class__.__name__}, {str(e)}")  
            
    async def close(self) -> bool:
        """`openhivenpy.gateway.HTTPClient.connect()`

        Closes the HTTP session that is currently connected to Hiven!
        
        """
        try:
            await self.session.close()
            self.http_ready = False
        except Exception as e:
            logger.error(f" An error occured while trying to close the HTTP Connection to Hiven: {sys.exc_info()[1].__class__.__name__}, {str(e)}")
            raise errs.HTTPError(f"Attempt to create session failed! Cause of Error: {sys.exc_info()[1].__class__.__name__}, {str(e)}")  
    
    async def raw_request(
                        self, 
                        endpoint: str, 
                        *, 
                        method: str = "GET", 
                        timeout: float = 15, 
                        **kwargs) -> aiohttp.ClientResponse:
        """`openhivenpy.gateway.HTTPClient.raw_request()`

        Wrapped HTTP request for a specified endpoint. 
        
        Returns the raw ClientResponse object
        
        Parameter:
        ----------
        
        endpoint: `str` - Url place in url format '/../../..' Will be appended to the standard link: 'https://api.hiven.io/version'
    
        json: `str` - JSON format data that will be appended to the request
        
        timeout: `int` - Time the server has time to respond before the connection timeouts. Defaults to 15
        
        method: `str` - HTTP Method that should be used to perform the request
        
        headers: `dict` - Defaults to the normal headers. Note: Changing conent type can make the request break. Use with caution!
                
        **kwargs: `any` - Other parameter for requesting. See https://docs.aiohttp.org/en/stable/client_reference.html#aiohttp.ClientSession for more info
        
        """
        # Timeout Handler that watches if the request takes too long
        async def _time_out_handler(timeout: float) -> None:
            start_time = time.time()
            timeout_limit = start_time + timeout
            while True:
                if self._request.done():
                    break
                elif time.time() > timeout_limit:
                    if not self._request.cancelled():
                        self._request.cancel()
                    logger.debug(f" [HTTP] >> FAILED HTTP '{method.upper()}' with endpoint: "
                                 f"{endpoint}; Request to Hiven timed out!")
                    break
                await asyncio.sleep(0.25)
            return None

        async def _request(endpoint, method, **kwargs):
            http_code = "Unknown Internal Error"
            # Deactivated because of errors that occured using it!
            timeout = aiohttp.ClientTimeout(total=None)
            if self.http_ready:
                try:
                    if kwargs.get('headers') == None:
                        headers = self.headers
                    else:
                        headers = kwargs.pop('headers')
                    url = f"{self.api_url}{endpoint}"
                    async with self.session.request(
                                                    method=method,
                                                    url=url,
                                                    headers=headers, 
                                                    timeout=timeout,
                                                    **kwargs) as resp:
                        http_code = resp.status
                        
                        if resp.status < 300:
                            data = await resp.read()
                            if resp.status == 204:
                                error = True
                                error_code = "Empty Response"
                                error_reason = "Got an empty response that cannot be converted to json!"
                            else:
                                json = json_decoder.loads(data)
                                
                                error = json.get('error', False)
                                if error:
                                    error_code = json['error']['code'] if json['error'].get('code') != None else 'Unknown HTTP Error'
                                    error_reason = json['error']['message'] if json['error'].get('message') != None else 'Possibly faulty request or response!'
                                else:
                                    error_code = 'Unknown HTTP Error'
                                    error_reason = 'Possibly faulty request or response!'

                            if resp.status == 200 or resp.status == 202:
                                if error == False:
                                    return resp
                                
                        error_code = resp.status
                        error_reason = resp.reason

                        logger.debug(f" [HTTP] << FAILED HTTP '{method.upper()}' with endpoint: " 
                                     f"{endpoint}; {error_code}, {error_reason}")
                        return resp
        
                except asyncio.TimeoutError as e:
                    logger.error(f" [HTTP] << FAILED HTTP '{method.upper()}' with endpoint: {endpoint}; Request to Hiven timed out!")

                except Exception as e:
                    logger.error(f" [HTTP] << FAILED HTTP '{method.upper()}' with endpoint: {endpoint}; {sys.exc_info()[1].__class__.__name__}, {str(e)}")
                        
            else:
                logger.error(f" [HTTP] << The HTTPClient was not ready when trying to HTTP {method}!" 
                             "The connection is either faulty initalized or closed!")
                return None    

        self._request = self.loop.create_task(_request(endpoint, method, **kwargs))
        _task_time_out_handler = self.loop.create_task(_time_out_handler(timeout))

        try:
            resp = await asyncio.gather(self._request, _task_time_out_handler)
        except asyncio.CancelledError:
            logger.debug(f" [HTTP] >> Request was cancelled!")
            return
        except Exception as e:
            logger.error(f" [HTTP] >> FAILED HTTP '{method.upper()}' with endpoint: {self.host}{endpoint}; {sys.exc_info()[1].__class__.__name__}, {str(e)}")
            raise errs.HTTPError(f"An error occured while performing HTTP '{method.upper()}' with endpoint: {self.host}{endpoint}; {sys.exc_info()[1].__class__.__name__}, {str(e)}")
        return resp[0]
    
    async def request(self, endpoint: str, *, json: dict = None, timeout: float = 15, **kwargs) -> dict:
        """`openhivenpy.gateway.HTTPClient.request()`

        Wrapped HTTP request for a specified endpoint. 
        
        Returns a python dictionary containing the response data if successful and else returns `None`
        
        Parameter:
        ----------
        
        endpoint: `str` - Url place in url format '/../../..' Will be appended to the standard link: 'https://api.hiven.io/version'
    
        json: `str` - JSON format data that will be appended to the request
        
        timeout: `int` - Time the server has time to respond before the connection timeouts. Defaults to 15
        
        headers: `dict` - Defaults to the normal headers. Note: Changing conent type can make the request break. Use with caution!
        
        **kwargs: `any` - Other parameter for requesting. See https://docs.aiohttp.org/en/stable/client_reference.html#aiohttp.ClientSession for more info
        
        """
        resp = await self.raw_request(endpoint, method="GET", timeout=timeout, **kwargs)
        if resp != None:
            return await resp.json()
        else:
            return None
    
    async def post(self, endpoint: str, *, json: dict = None, timeout: float = 15, **kwargs) -> aiohttp.ClientResponse:
        """`openhivenpy.gateway.HTTPClient.post()`

        Wrapped HTTP Post for a specified endpoint.
        
        Returns the ClientResponse object if successful and else returns `None`
        
        Parameter:
        ----------
        
        endpoint: `str` - Url place in url format '/../../..' Will be appended to the standard link: 'https://api.hiven.io/version'
    
        json: `str` - JSON format data that will be appended to the request
        
        timeout: `int` - Time the server has time to respond before the connection timeouts. Defaults to 15
        
        headers: `dict` - Defaults to the normal headers. Note: Changing conent type can make the request break. Use with caution!
        
        **kwargs: `any` - Other parameter for requesting. See https://docs.aiohttp.org/en/stable/client_reference.html#aiohttp.ClientSession for more info
        
        """
        return await self.raw_request(
                                    endpoint, 
                                    method="POST", 
                                    json=json, 
                                    timeout=timeout, 
                                    headers=headers, 
                                    **kwargs)
            
    async def delete(self, endpoint: str, *, timeout: int = 10, **kwargs) -> aiohttp.ClientResponse:
        """`openhivenpy.gateway.HTTPClient.delete()`

        Wrapped HTTP delete for a specified endpoint.
        
        Returns the ClientResponse object if successful and else returns `None`
        
        Parameter:
        ----------
        
        endpoint: `str` - Url place in url format '/../../..' Will be appended to the standard link: 'https://api.hiven.io/version'
    
        json: `str` - JSON format data that will be appended to the request
        
        timeout: `int` - Time the server has time to respond before the connection timeouts. Defaults to 15
        
        headers: `dict` - Defaults to the normal headers. Note: Changing conent type can make the request break. Use with caution!
        
        **kwargs: `any` - Other parameter for requesting. See https://docs.aiohttp.org/en/stable/client_reference.html#aiohttp.ClientSession for more info

        """
        return await self.raw_request(
                                    endpoint, 
                                    method="DELETE", 
                                    timeout=timeout, 
                                    **kwargs)
        
    async def put(self, endpoint: str, *, json: dict = None, timeout: float = 15, **kwargs) -> aiohttp.ClientResponse:
        """`openhivenpy.gateway.HTTPClient.put()`

        Wrapped HTTP put for a specified endpoint.
        
        Similar to post, but multiple requests do not affect performance
        
        Returns the ClientResponse object if successful and else returns `None`
        
        Parameter:
        ----------
        
        endpoint: `str` - Url place in url format '/../../..' Will be appended to the standard link: 'https://api.hiven.io/version'
    
        json: `str` - JSON format data that will be appended to the request
        
        timeout: `int` - Time the server has time to respond before the connection timeouts. Defaults to 15
        
        headers: `dict` - Defaults to the normal headers. Note: Changing conent type can make the request break. Use with caution!
        
        **kwargs: `any` - Other parameter for requesting. See https://docs.aiohttp.org/en/stable/client_reference.html#aiohttp.ClientSession for more info

        """
        return await self.raw_request(
                                    endpoint, 
                                    method="PUT", 
                                    json=json, 
                                    timeout=timeout, 
                                    headers=headers,
                                    **kwargs)
        
    async def patch(self, endpoint: str, *, json: dict = None, timeout: float = 15, **kwargs) -> aiohttp.ClientResponse:
        """`openhivenpy.gateway.HTTPClient.patch()`

        Wrapped HTTP patch for a specified endpoint.
        
        Returns the ClientResponse object if successful and else returns `None`
        
        Parameter:
        ----------
        
        endpoint: `str` - Url place in url format '/../../..' Will be appended to the standard link: 'https://api.hiven.io/version'
    
        json: `str` - JSON format data that will be appended to the request
        
        timeout: `int` - Time the server has time to respond before the connection timeouts. Defaults to 15
        
        headers: `dict` - Defaults to the normal headers. Note: Changing conent type can make the request break. Use with caution!
        
        **kwargs: `any` - Other parameter for requesting. See https://docs.aiohttp.org/en/stable/client_reference.html#aiohttp.ClientSession for more info

        """
        return await self.raw_request(
                                    endpoint, 
                                    method="PATCH", 
                                    json=json, 
                                    timeout=timeout, 
                                    headers=headers,
                                    **kwargs)
    
    async def options(self, endpoint: str, *, json: dict = None, timeout: float = 15, **kwargs) -> aiohttp.ClientResponse:
        """`openhivenpy.gateway.HTTPClient.options()`

        Wrapped HTTP options for a specified endpoint.
        
        Requests permission for performing communication with a URL or server
        
        Returns the ClientResponse object if successful and else returns `None`
        
        Parameter:
        ----------
        
        endpoint: `str` - Url place in url format '/../../..' Will be appended to the standard link: 'https://api.hiven.io/version'
    
        json: `str` - JSON format data that will be appended to the request
        
        timeout: `int` - Time the server has time to respond before the connection timeouts. Defaults to 15
        
        headers: `dict` - Defaults to the normal headers. Note: Changing conent type can make the request break. Use with caution!
        
        **kwargs: `any` - Other parameter for requesting. See https://docs.aiohttp.org/en/stable/client_reference.html#aiohttp.ClientSession for more info
        
        """
        return await self.raw_request(
                                    endpoint, 
                                    method="OPTIONS", 
                                    json=json, 
                                    timeout=timeout, 
                                    **kwargs)
    