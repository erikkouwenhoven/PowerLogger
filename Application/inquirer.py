from datetime import datetime
from DataHolder.data_holder import DataHolder
from Application.plugin import Plugin
from Application.Plugins.p1_plugin import P1Plugin


class Inquirer:
    """

    """

    def __init__(self, data_holder: DataHolder, plugins: list[Plugin]):
        self.data_holder = data_holder
        self.plugins = plugins

    def get_P1_start_time(self) -> datetime:
        if p1_interface := self.get_P1_interface():
            return p1_interface.interpreter.start_time

    def get_P1_clock(self):
        if p1_interface := self.get_P1_interface():
            p1_sample = p1_interface.get_current_sample()
            return p1_sample.get_timestamp()

    def get_P1_interface(self):
        for plugin in self.plugins:
            if plugin.plugin_name == P1Plugin.plugin_name:
                return getattr(plugin, "p1_interface")
