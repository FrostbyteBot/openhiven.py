"""
Exceptions used specifically for the module OpenHiven.py

---

Under MIT License

Copyright © 2020 - 2021 Nicolas Klatzer

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


__all__ = [
    'HivenError', 'HivenConnectionError', 'HivenENVError',

    'ClientTypeError', 'SessionCreateError', 'UnknownEventError',
    'InvalidTokenError', 'ClosingError', 'NoneClientType',

    'HivenGatewayError', 'WebSocketMessageError', 'WebSocketFailedError',
    'WebSocketClosedError', 'RestartSessionError',

    'HTTPError', 'HTTPRequestTimeoutError', 'HTTPFailedRequestError', 'HTTPForbiddenError',
    'HTTPResponseError', 'HTTPReceivedNoDataError',

    'InitializationError', 'InvalidPassedDataError',

    'ExecutionLoopError', 'ExecutionLoopStartError',

    'CommandError'
]


# -------- CORE --------


class HivenError(Exception):
    """
    Base Exception in the openhivenpy library!
    
    All other exceptions inherit from this base class
    """
    error_msg = None

    def __init__(self, *args):
        if self.error_msg is None or args:
            if args:
                self.error_msg = ", ".join([str(arg) for arg in args])
            else:
                self.error_msg = f"Exception occurred in the package openhivenpy"

        super().__init__(self.error_msg)
        
    def __str__(self):
        return self.error_msg

    def __repr__(self):
        return "<{} error_msg={}>".format(self.__class__.__name__, self.error_msg)

    def __call__(self):
        return str(self)


class HivenConnectionError(HivenError):
    """ The connection to Hiven failed to be kept alive or started! """
    error_msg = "The connection to Hiven failed to be kept alive or started!"


class HivenENVError(HivenError):
    """ The connection to Hiven failed to be kept alive or started! """
    error_msg = "Failed to load .env file of the module!"


class ClientTypeError(HivenError):
    """ Invalid client type was passed resulting in a failed initialisation! """
    error_msg = "Invalid client type was passed resulting in a failed initialization!"


class SessionCreateError(HivenConnectionError):
    """ Failed to create Session! """
    error_msg = "Failed to create Session!"


class UnknownEventError(HivenError):
    """ The attempt to register an event failed due to the specified event_listener not being found! """
    error_msg = "Failed to find event of the registered EventListener"


class InvalidTokenError(HivenError):
    """ Invalid Token was passed! """
    error_msg = "Invalid Token was passed!"


class ClosingError(HivenConnectionError):
    """ The client is unable to close the connection to Hiven! """
    error_msg = "Failed to close Connection!"


class NoneClientType(Warning):
    """ A None Type was passed in the Initialization! """
    error_msg = ("A None ClientType was passed! This can indicate faulty usage of the Client and could lead to errors"
               "while running!")


# -------- GATEWAY --------


class HivenGatewayError(HivenConnectionError):
    """ General Exception in the Gateway and Connection to Hiven! """
    error_msg = "Encountered and Exception in the Hiven Gateway!"


# -------- WEBSOCKET --------

class WebSocketMessageError(HivenGatewayError):
    """ An Exception occurred while handling a message/response from Hiven """
    error_msg = "Failed to handle WebSocket Message!"


class WebSocketFailedError(HivenGatewayError):
    """ Received an exception call  """
    error_msg = "Received Error frame from the aiohttp Websocket which resulted in the crashing of the WebSocket!"


class WebSocketClosedError(HivenError):
    """ The Hiven WebSocket was closed and an exception is raised to stop the current processes """
    error_msg = "The Hiven WebSocket is closing!"


class RestartSessionError(HivenGatewayError):
    """ Exception used to trigger restarts in the gateway module """
    error_msg = "Restarting the Session and re-initialising the data!"


# -------- HTTP --------


class HTTPError(HivenGatewayError):
    """ Base Exception for exceptions in the HTTP and overall requesting """
    error_msg = "Failed to perform request! Code: {}! See HTTP logs!"

    def __init__(self, *args, code="Unknown"):
        if args:
            arg = "".join([str(arg) for arg in args])
        else:
            arg = self.error_msg.format(code)
        super().__init__(arg)


class HTTPRequestTimeoutError(HTTPError):
    """ The sent request did not finish in time and raised a timeout exception """
    error_msg = "Failed to perform request in time!"

    def __init__(self, *args):
        if args:
            arg = "".join([str(arg) for arg in args])
        else:
            arg = self.error_msg
        super().__init__(arg)


class HTTPFailedRequestError(HTTPError):
    """ General Exception for errors while handling a request """


class HTTPForbiddenError(HTTPFailedRequestError):
    """ The client was forbidden to perform a Request """
    error_msg = "The client was forbidden to execute a certain task or function!"


class HTTPResponseError(HTTPError):
    """ Response was in wrong format or expected data was not received """
    error_msg = "Failed to handle Response and utilise data! Code: {}! See HTTP logs!"


class HTTPReceivedNoDataError(HTTPError):
    """
    Received a response without the required data field or
    received a 204(No Content) in a request that expected data.
    """
    error_msg = "Response does not contain the expected Data! Code: {}! See HTTP logs!"


# -------- DATA --------

class InitializationError(HivenError):
    """ The object failed to initialise """
    error_msg = "The object failed to initialise"


class InvalidPassedDataError(InitializationError):
    """ Failed to utilise data as wanted due to missing or unexpected data! """
    def __init__(self, *args, data):
        if args:
            arg = "".join([str(arg) for arg in args])
        else:
            arg = "The initializer failed to validate and utilise the data likely due to wrong data passed!"

        if data:
            arg += f"\n Data: {data}"
        super().__init__(arg)


# -------- ExecutionLoop --------


class ExecutionLoopError(HivenError):
    """ An exception occurred in the execution loop running parallel to the core """
    error_msg = "An exception occurred in the execution loop running parallel to the core"


class ExecutionLoopStartError(HivenError):
    """ The execution failed to start and crashed """
    error_msg = "Failed to start the Execution Loop"


# -------- COMMAND --------


class CommandError(HivenError):
    """ General Exception while executing a command function on Hiven! """
    error_msg = "An Exception occurred while executing a command on Hiven!"
