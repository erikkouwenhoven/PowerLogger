from abc import ABC, abstractmethod


class Plugin(ABC):
    """
    A Plugin is an add-on to the core application, that may or may nor be activated.
    Subclasses of Plugin get informed on subscribed events. The Plugin is identified by a unique name. The plugin should
    handle an update with a key that was defined at registration.
    """

    def __init__(self, plugin_name, publisher, event_keys: tuple[str]):
        self.plugin_name = plugin_name
        self.publisher = publisher
        for key in event_keys:
            publisher.register(self, key)

    @abstractmethod
    def update(self, event_key, data):
        assert self in self.publisher.subscriptions
        assert event_key in self.publisher.subscriptions[self]
        pass


class Publisher:
    """
    Publish-subscribe (pubsub) pattern, see
    https://morkrispil.wordpress.com/2015/07/16/python-design-patterns-5-observer-aka-pub-sub/.
    The publisher maintains a collection of Plugins, i.e. a dict with (key=plugin, value=list with event keys).
    A Plugin registers itself to the Publisher at construction for getting informed when events occur of the type
    registered for. The Plugin then gets a call to its update function.

    A plugin may publish an event, resulting in an update of registered plugins for that particular event.
    """

    def __init__(self):
        self.subscriptions: dict[Plugin, list[str]] = {}

    def register(self, subscriber: Plugin, event_key: str):
        if subscriber not in self.subscriptions:
            self.subscriptions[subscriber] = []
        self.subscriptions[subscriber].append(event_key)

    def unregister(self, subscriber: Plugin):
        del self.subscriptions[subscriber]

    def publish(self, event_key: str, data):
        for subscriber in self.subscriptions:
            if event_key in self.subscriptions[subscriber]:
                subscriber.update(event_key, data)

    def get_plugin(self, plugin_name: str) -> Plugin | None:
        for plugin in self.subscriptions:
            if plugin.plugin_name == plugin_name:
                return plugin

    def get_listeners(self, event_key: str) -> list[Plugin]:
        return [subscriber for subscriber, subscribed_events in self.subscriptions.items() if
                event_key == '*' or event_key in subscribed_events]

    def get_plugins(self) -> list[Plugin]:
        return [subscriber for subscriber in self.subscriptions]
