from datetime import datetime

from assistant.memory.events.event import (
    MemoryEvent,
)
from assistant.memory.events.listener import (
    MemoryEventListener,
)
from assistant.memory.events.publisher import (
    MemoryEventPublisher,
)


class FakeListener(
    MemoryEventListener
):

    def __init__(self):
        self.events = []

    def handle(
        self,
        event: MemoryEvent,
    ) -> None:

        self.events.append(event)


def create_event():

    return MemoryEvent(
        event_id="event-1",
        created_at=datetime.now(),
        event_type="memory_created",
        memory_id="memory-1",
        resolution=None,
        action="create",
        content="I prefer Python.",
        success=True,
    )


def test_publisher_notifies_listener():

    listener = FakeListener()

    publisher = MemoryEventPublisher(
        listeners=[listener]
    )

    event = create_event()

    publisher.publish(event)

    assert len(listener.events) == 1
    assert listener.events[0] == event


def test_publisher_can_subscribe():

    publisher = MemoryEventPublisher()

    listener = FakeListener()

    publisher.subscribe(listener)

    publisher.publish(
        create_event()
    )

    assert len(listener.events) == 1


def test_multiple_listeners_receive_event():

    first = FakeListener()
    second = FakeListener()

    publisher = MemoryEventPublisher(
        listeners=[
            first,
            second,
        ]
    )

    event = create_event()

    publisher.publish(event)

    assert first.events == [event]
    assert second.events == [event]


class BrokenListener(
    MemoryEventListener
):
    def handle(
            self,
            event: MemoryEvent,
    ) -> None:
        raise RuntimeError(
            "Listener failed"
        )


def test_broken_listener_does_not_stop_other_listeners():

    broken = BrokenListener()
    working = FakeListener()

    publisher = MemoryEventPublisher(
        listeners=[
            broken,
            working,
        ]
    )

    event = create_event()

    publisher.publish(event)

    assert working.events == [event]
