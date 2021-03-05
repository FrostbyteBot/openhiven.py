import asyncio
import logging

__all__ = ['DynamicEventBuffer', 'MessageBroker']

logger = logging.getLogger(__name__)


class DynamicEventBuffer(list):
    def __init__(self, event: str, *args, **kwargs):
        self.event = event
        super().__init__(*args, **kwargs)

    def add(self, data: dict, *args, **kwargs):
        self.append(
            {
                'data': data,
                'args': args,
                'kwargs': kwargs
            })

    def get_next_event(self) -> dict:
        """ Fetches the event at index 0. Raises an exception if the buffer is empty! """
        return self.pop(0)


class MessageBroker:
    """ Message Broker that will store the messages in queues """
    def __init__(self, client):
        self.event_queues = {}
        self.client = client
        self.event_consumer = EventConsumer(self)
        self.running_loop = None

    @property
    def running(self):
        if self.running_loop:
            return not getattr(self.running_loop, 'done')()
        else:
            return False

    def create_buffer(self, event: str) -> DynamicEventBuffer:
        new_buffer = DynamicEventBuffer(event)
        self.event_queues[event] = new_buffer
        return new_buffer

    def get_buffer(self, event: str) -> DynamicEventBuffer:
        """ Tries to fetch a buffer from the cache. If the buffer is not found a new one will be created

        :return: The fetched or newly created buffer instance
        """
        buffer = self.event_queues.get(event)
        if buffer:
            return buffer
        else:
            return self.create_buffer(event)

    async def run(self):
        """ Runs the Event Consumer instance which stores the workers for all event_listeners """
        self.running_loop = asyncio.create_task(self.event_consumer.process_loop())
        await self.running_loop


class Worker:
    """ Worker class that runs the Event Listeners"""
    def __init__(self, event: str, message_broker):
        self.event = event
        self.message_broker = message_broker
        self.client = message_broker.client
        self.queuing = self.client.queuing

    @property
    def event_buffer(self):
        return self.message_broker.event_queues.get(self.event)

    async def exec(self, tasks):
        """ Executes all passed event_listener tasks parallel """
        await asyncio.gather(*tasks)

    async def run_one_sequence(self):
        """ Fetches an event from the buffer and runs all current Event Listeners """
        if self.event_buffer:
            # Fetching the event data, args and kwargs from the buffer
            event = self.event_buffer.get_next_event()
            data = event['data']
            args = event['args']
            kwargs = event['kwargs']

            # Creating a new future for every active listener
            tasks = [e(data, *args, **kwargs) for e in self.client.active_listeners[self.event]]

            # if queuing is active running a sequence will not return until all event_listeners were dispatched
            # without queuing all tasks will be assigned to the asyncio event_loop and the function will return
            if self.queuing:
                await self.exec(tasks)
            else:
                asyncio.create_task(self.exec(tasks))
        else:
            return


class EventConsumer:
    """ Dispatcher which will fetch events and execute them in a loop """
    def __init__(self, message_broker):
        self.workers = {}
        self.message_broker = message_broker
        self.client = message_broker.client

    def create_worker(self, event):
        """ Creates a new worker that can execute event_listeners """
        worker = Worker(event, self.message_broker)
        self.workers[event] = worker
        return worker

    async def process_loop(self):
        while self.client.connection_status not in ("CLOSING", "CLOSED"):
            # Running the worker for every event_buffer that is not empty and therefore contains not triggered events
            for event, val in self.message_broker.event_queues.items():
                # Avoiding empty queues
                if val:
                    worker = self.workers.get(event)
                    if not worker:
                        worker = self.create_worker(event)
                    asyncio.create_task(worker.run_one_sequence())
            await asyncio.sleep(0.05)