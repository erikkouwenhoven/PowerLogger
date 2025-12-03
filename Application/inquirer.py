from datetime import datetime
from typing import Type
from Application.domain_rules import solar_efficiency, Grid3phases
from DataHolder.buffer_attrs import Persistency
from DataHolder.data_holder import DataHolder
from Utils.time_delay import Period
from Application.Plugins.plugin import Plugin
from Application.Plugins.p1_plugin import P1Plugin
from Application.processor import Processor


class Inquirer:
    """

    """

    def __init__(self, data_holder: DataHolder, plugins: list[Plugin]):
        self.data_holder = data_holder
        self.plugins = plugins

    def get_P1_start_time(self) -> datetime | None:
        if p1_interface := self.get_P1_interface():
            return p1_interface.interpreter.start_time

    def get_P1_clock(self):
        if p1_interface := self.get_P1_interface():
            p1_sample = p1_interface.get_current_sample()
            try:
                return p1_sample.get_timestamp()
            except AttributeError:
                return None

    def get_recent_data(self, data_store_name: str, signals: list[str]) -> tuple[float, dict[str, tuple[float, str]]] | None:
        """
        Geeft timestamp en dict (key is gegeven signal) met waarde en eenheid van de gevraagde signalen
        """
        if data_store := self.data_holder.data_store(data_store_name):
            if last_data_item := data_store.data.get_data_item(data_store.data.last_index()):
                return last_data_item.get_timestamp(), {signal: (last_data_item.get_value(signal), last_data_item.get_unit(signal)) for signal in signals}

    def get_summed_data(self, data_store_name: str, signals: list[str], period: Type[Period]) -> tuple[float, dict[str, tuple[float, str]]] | None:
        if data_store := self.data_holder.data_store(data_store_name):
            data_item = Processor.average_integrate(data_store.data, period.start_time(), datetime.now(), datetime.now(), signals, avg=False)
            return data_item.get_timestamp(), {signal: (data_item.get_value(signal), data_item.get_unit(signal)) for signal in signals}

    def get_performance_info(self, period: Period | None) -> tuple[float | None, Grid3phases | None, float | None]:
        """
        Geeft de volgende data
            zon
            zon-efficientie
            net_grid
        op basis van een periode. Periode None komt overeen met VALUE
            VALUE
            SUM HOUR
            SUM TODAY
            SUM MONTH
            SUM THISYEAR
        """
        solar_value = None
        grid_3phases = None
        solar_eff = None
        # voor de VALUE zoek de volatile datastore die de gevraagde signals bevat
        solar_signals = ['SOLAR']
        if period is None:
            if solar_data_store := self.data_holder.filter(solar_signals, req_persistency=Persistency.Volatile):
                res = self.get_recent_data(solar_data_store.name, solar_signals)
            else:
                res = None
        else:
            if solar_data_store := self.data_holder.filter(solar_signals, req_time_span=period):
                res = self.get_summed_data(solar_data_store.name, solar_signals, period)
            else:
                res = None
        if res:
            solar_value = res[1][solar_signals[0]][0]

        signals = ['NET_USAGE', 'NET_PRODUCTION']
        if period is None:
            if signals_data_store := self.data_holder.filter(signals, req_persistency=Persistency.Volatile):
                res = self.get_recent_data(signals_data_store.name, signals)
            else:
                res = None
        else:
            if signals_data_store := self.data_holder.filter(signals, req_time_span=period):
                res = self.get_summed_data(signals_data_store.name, signals, period)
            else:
                res = None
        if res:
            grid_3phases = Grid3phases(current_usage = res[1]['NET_USAGE'][0],
                                   current_production = res[1]['NET_PRODUCTION'][0])
        if solar_value and grid_3phases:
            solar_eff = solar_efficiency(solar_value, grid_3phases)
        return solar_value, grid_3phases, solar_eff

    def get_P1_interface(self):
        for plugin in self.plugins:
            if plugin.plugin_name == P1Plugin.plugin_name:
                return getattr(plugin, "p1_interface")
