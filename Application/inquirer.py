from typing import List, Union
from datetime import datetime
from DataHolder.data_holder import DataHolder
from Application.plugin import Plugin
from Application.Plugins.p1_plugin import P1Plugin


class Inquirer:
    """

    """

    def __init__(self, data_holder: DataHolder, plugins: List[Plugin]):
        self.data_holder = data_holder
        self.plugins = plugins

    def get_P1_start_time(self) -> datetime:
        if p1_interface := self.get_P1_interface():
            return p1_interface.interpreter.start_time

    def get_P1_clock(self):
        if p1_interface := self.get_P1_interface():
            p1_sample = p1_interface.get_current_sample()
            try:
                return p1_sample.get_timestamp()
            except AttributeError:
                return None

    def get_recent_data(self, data_store_name: str, signals: List[str]) -> List[Union[str, float]]:
        """
        Geeft een lijst van float (eerste element is timestamp) en strings met waarde en eenheid van de gevraagde signalen
        """
        if data_store := self.data_holder.data_store(data_store_name):
            if last_data_item := data_store.data.get_data_item(data_store.data.last_index()):
                return [last_data_item.get_timestamp()] + [last_data_item.get_value_and_unit(signal) for signal in signals]
                # return last_data_item.to_array(signals)

    def get_P1_interface(self):
        for plugin in self.plugins:
            if plugin.plugin_name == P1Plugin.plugin_name:
                return getattr(plugin, "p1_interface")
