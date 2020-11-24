import logging
import sys

import openhivenpy.exceptions as errs
from openhivenpy.gateway.http import HTTPClient
from ._get_type import getType

logger = logging.getLogger(__name__)

class Context():
    """`openhivenpy.types.Context` 
    
    Data Class for a Command or Event Context
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    The class inherits all the avaible data from Hiven(attr -> read-only)!
    
    Returned with events, commands and HivenClient.on_ready()
    
    """
    def __init__(self, data: dict, http_client: HTTPClient):
        self._http_client = http_client