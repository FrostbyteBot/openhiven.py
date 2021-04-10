import logging
import sys
import asyncio
import types
import typing
import fastjsonschema

from . import HivenObject, check_valid
from .message import Message
from .house import House
from .. import utils
from .. import exceptions as errs

logger = logging.getLogger(__name__)

__all__ = ['Room']


class Room(HivenObject):
    """
    Represents a Hiven Room inside a House

    ---

    Possible Types:

    0 - Text

    1 - Portal

    """
    schema = {
        'type': 'object',
        'properties': {
            'id': {'type': 'string'},
            'name': {'type': 'string'},
            'house_id': {'type': 'string'},
            'position': {'type': 'integer'},
            'type': {'type': 'integer'},
            'emoji': {
                'anyOf': [
                    {'type': 'object'},
                    {'type': 'null'}
                ],
                'default': None
            },
            'description': {
                'anyOf': [
                    {'type': 'string'},
                    {'type': 'null'}
                ],
                'default': None
            },
            'last_message_id': {
                'anyOf': [
                    {'type': 'string'},
                    {'type': 'null'}
                ],
                'default': None
            },
            'house': {
                'anyOf': [
                    {'type': 'string'},
                    {'type': 'object'},
                    {'type': 'null'}
                ],
            },
            'permission_overrides': {'default': None},
            'default_permission_override': {'default': None},
            'recipients': {'default': None},
            'owner_id': {
                'anyOf': [
                    {'type': 'string'},
                    {'type': 'null'}
                ],
                'default': None
            },
        },
        'additionalProperties': False,
        'required': ['id', 'name', 'house_id', 'type']
    }
    json_validator: types.FunctionType = fastjsonschema.compile(schema)

    def __init__(self, **kwargs):
        self._id = kwargs.get('id')
        self._name = kwargs.get('name')
        self._house_id = kwargs.get('house_id')
        self._position = kwargs.get('position')
        self._type = kwargs.get('type')
        self._emoji = kwargs.get('emoji')
        self._description = kwargs.get('description')
        self._last_message_id = kwargs.get('last_message_id')
        self._house = kwargs.get('house')

    def __repr__(self) -> str:
        info = [
            ('name', repr(self.name)),
            ('id', self.id),
            ('house_id', self.house_id),
            ('position', self.position),
            ('type', self.type),
            ('emoji', self.emoji),
            ('description', self.description)
        ]
        return str('<Room {}>'.format(' '.join('%s=%s' % t for t in info)))

    def get_cached_data(self) -> typing.Union[dict, None]:
        """ Fetches the most recent data from the cache based on the instance id """
        return self._client.storage['rooms']['house'][self.id]

    @classmethod
    @check_valid()
    def format_obj_data(cls, data: dict) -> dict:
        """
        Validates the data and appends data if it is missing that would be required for the creation of an
        instance.

        :param data: Dict for the data that should be passed
        :return: The modified dictionary
        """
        data = cls.validate(data)
        return data

    @classmethod
    def _insert_data(cls, data: dict, client):
        """
        Creates an instance of the Room Class with the passed data
        (Needs to be already validated/formed and populated with the wanted data -> objects should be ids)

        ---

        Does not update the cache and only read from it!
        Only intended to be used to create a instance to interact with Hiven!

        :param data: Dict for the data that should be passed
        :param client: Client used for accessing the cache
        :return: The newly constructed Room Instance
        """
        try:
            data['house'] = House._insert_data(
                client.storage['houses'][data['house_id']], client
            )
            instance = cls(**data)

        except Exception as e:
            utils.log_traceback(
                msg=f"Traceback in function '{cls.__name__}' Validation:",
                suffix=f"Failed to initialise {cls.__name__} due to exception:\n{sys.exc_info()[0].__name__}: {e}!"
            )
            raise errs.InitializationError(f"Failed to initialise {cls.__name__} due to exception:\n"
                                           f"{sys.exc_info()[0].__name__}: {e}!")
        else:
            instance._client = client
            return instance

    @property
    def id(self) -> str:
        return getattr(self, '_id', None)

    @property
    def name(self) -> str:
        return getattr(self, '_name', None)

    @property
    def house_id(self) -> str:
        return getattr(self, '_house_id', None)

    @property
    def house(self) -> House:
        return getattr(self, '_house', None)

    @property
    def position(self) -> int:
        return getattr(self, '_position', None)

    @property
    def type(self) -> int:
        return getattr(self, '_type', None)

    @property
    def emoji(self) -> str:
        return getattr(self, '_emoji', None)

    @property
    def description(self) -> typing.Union[str, None]:
        return getattr(self, '_description', None)

    async def send(self, content: str, delay: float = None) -> typing.Union[Message, None]:
        """
        Sends a message in the current room.
        
        :param content: Content of the message
        :param delay: Seconds to wait until sending the message (in seconds)
        :return: A new message object if the request was successful
        """
        try:
            if delay is not None:
                await asyncio.sleep(delay=delay)
            resp = await self._client.http.post(f"/rooms/{self.id}/messages", json={"content": content})
            raw_data = await resp.json()

            # Raw_data not in correct format => needs to access data field
            data = raw_data.get('data')
            data = Message.format_obj_data(data)
            return Message._insert_data(data, self._client)

        except Exception as e:
            utils.log_traceback(msg="[ROOM] Traceback:",
                                suffix=f"Failed to send message in room {repr(self)}: \n"
                                       f"{sys.exc_info()[0].__name__}: {e}")
            return None

    async def edit(self, **kwargs) -> bool:
        """
        Changes the rooms data on Hiven

        Available options: emoji, name, description

        :return: True if the request was successful else False
        """
        try:
            for key in kwargs.keys():
                if key in ['emoji', 'name', 'description']:
                    await self._client.http.patch(f"/rooms/{self.id}", json={key: kwargs.get(key)})

                    return True
                else:
                    raise NameError("The passed value does not exist in the Room!")

        except Exception as e:
            keys = "".join(key + " " for key in kwargs.keys()) if kwargs != {} else ''

            utils.log_traceback(msg="[ROOM] Traceback:",
                                suffix=f"Failed to change the values {keys} in room {repr(self)}: \n"
                                       f"{sys.exc_info()[0].__name__}: {e}")
            return False

    async def start_typing(self) -> bool:
        """
        Adds the client to the list of users typing
            
        :return: True if the request was successful else False
        """
        try:
            await self._client.http.post(f"/rooms/{self.id}/typing")

            return True

        except Exception as e:
            utils.log_traceback(msg="[ROOM] Traceback:",
                                suffix=f"Failed to create invite for house {self.name} with id {self.id}: \n"
                                       f"{sys.exc_info()[0].__name__}: {e}")
            return False

    async def get_recent_messages(self) -> typing.Union[list, Message, None]:
        """
        Gets the recent messages from the current room
            
        :return: A list of all messages in form of Message instances if successful.
        """
        try:
            raw_data = await self._client.http.get(f"/rooms/{self.id}/messages")
            raw_data = await raw_data.json()

            data = raw_data.get('data')

            messages_ = []
            for d in data:
                msg = d.Message.insert_data(d, self._client)
                messages_.append(msg)

            return messages_

        except Exception as e:
            utils.log_traceback(msg="[ROOM] Traceback:",
                                suffix=f"Failed to create invite for house {self.name} with id {self.id}: \n"
                                       f"{sys.exc_info()[0].__name__}: {e}")
            return None
