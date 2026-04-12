from __future__ import annotations
from dataclasses import dataclass
import logging
from datetime import datetime
from Application.domain_rules import Grid3phases
from DataHolder.buffer_attrs import Persistency
from DataHolder.data_holder import DataHolder
from Utils.time_delay import Period
from Application.Plugins.plugin import Plugin
from Application.Plugins.p1_plugin import P1Plugin
from Application.processor import Processor
from Utils.unit_handling import Unit, UnitHandler


class Inquirer:
    """

    """

    def __init__(self, data_holder: DataHolder, plugins: list[Plugin]):
        self.data_holder = data_holder
        self.plugins = plugins

    def get_P1_start_time(self) -> datetime | None:
        if p1_interface := self.get_P1_interface():
            return p1_interface.interpreter.start_time
        return None

    def get_P1_clock(self):
        if p1_interface := self.get_P1_interface():
            p1_sample = p1_interface.get_current_sample()
            try:
                return p1_sample.get_timestamp()
            except AttributeError:
                return None

    def get_recent_data(self, data_store_name: str, signals: list[str]) -> DataFragment | None:
        """
        Geeft timestamp en dict (key is gegeven signal) met waarde en eenheid van de gevraagde signalen
        """
        if data_store := self.data_holder.data_store(data_store_name):
            if storage := data_store.data:
                if last_data_item := storage.get_data_item(storage.last_index()):
                    if timestamp := last_data_item.get_timestamp():
                        return DataFragment(timestamp,
                                        {signal: (last_data_item.get_value(signal), last_data_item.get_unit(signal)) for signal in signals})
        return None

    def get_summed_data(self, data_store_name: str, signals: list[str], period: Period) -> DataFragment | None:
        if data_store := self.data_holder.data_store(data_store_name):
            if storage := data_store.data:
                data_item = Processor.average_integrate(storage, period.start_time(), datetime.now(), datetime.now(), signals, avg=False)
                if timestamp := data_item.get_timestamp():
                    return DataFragment(timestamp, {signal: (data_item.get_value(signal), data_item.get_unit(signal)) for signal in signals})
        return None

    def get_performance_info(self, period: Period | None) -> SolarEfficiency:
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
        # voor de VALUE zoek de volatile datastore die de gevraagde signals bevat
        solar_signal = 'SOLAR'
        if period is None:
            if solar_data_store := self.data_holder.filter([solar_signal], {"Persistency": Persistency.Volatile}):
                data_fragment = self.get_recent_data(solar_data_store.name, [solar_signal])
            else:
                data_fragment = None
        else:
            if solar_data_store := self.data_holder.filter([solar_signal], {"Time_span": period}):
                data_fragment = self.get_summed_data(solar_data_store.name, [solar_signal], period)
            else:
                data_fragment = None
        if data_fragment:
            solar_value = data_fragment.get_value(solar_signal)
            solar_unit = data_fragment.get_unit(solar_signal)
        else:
            solar_value = None
            solar_unit = None
        logging.debug(f"Solar value = {solar_value}")

        signals = ['NET_USAGE', 'NET_PRODUCTION']
        if period is None:
            if signals_data_store := self.data_holder.filter(signals):  # TODO hier zou je moeten vragen naar de datastore met kortste tijdsduur
                logging.debug(f"immediate: signals_data_store = {signals_data_store.name}")
                data_fragment = self.get_recent_data(signals_data_store.name, signals)
            else:
                logging.debug(f"immediate: signals_data_store = None")
                data_fragment = None
        else:
            if signals_data_store := self.data_holder.filter(signals, {"Time_span": period}):
                logging.debug(f"summing over period: signals_data_store = {signals_data_store.name}")
                data_fragment = self.get_summed_data(signals_data_store.name, signals, period)
            else:
                logging.debug(f"summing over period: signals_data_store = None")
                data_fragment = None
        logging.debug(f"Net data fragment = {data_fragment}")
        if data_fragment:
            assert data_fragment.get_unit('NET_USAGE') == data_fragment.get_unit('NET_PRODUCTION')
            if unit_str := data_fragment.get_unit('NET_USAGE'):
                unit = Unit(unit_str)
            else:
                unit = None
            grid_3phases = Grid3phases(current_usage = data_fragment.get_value('NET_USAGE'),
                                       current_production = data_fragment.get_value('NET_PRODUCTION'),
                                       unit=unit)
        else:
            grid_3phases = None
        return SolarEfficiency(period, solar_value, Unit(solar_unit) if solar_unit is not None else None, grid_3phases)

    def get_P1_interface(self):
        for plugin in self.plugins:
            if plugin.plugin_name == P1Plugin.plugin_name:
                return getattr(plugin, "p1_interface")


class DataFragment:

    def __init__(self, timestamp: float, signal_values: dict[str, tuple[float | None, str | None]]):
        self.timestamp = timestamp
        self.signal_values: dict[str, tuple[float | None, str | None]] = signal_values

    def get_value(self, signal: str) -> float | None:
        return self.signal_values[signal][0]

    def get_unit(self, signal: str) -> str | None:
        return self.signal_values[signal][1]

    def __repr__(self):
        return (f"DataFragment: t = {self.timestamp} signal_values = "
                f"{[f'{signal}: {self.signal_values[signal][0]} {self.signal_values[signal][1]}' for signal in self.signal_values]}")


@dataclass
class SolarEfficiency:
    period: Period | None = None
    solar_value: float | None = None
    solar_unit: Unit | None = None
    grid_3phases: Grid3phases | None = None

    def __repr__(self):
        """
            zon
            terugleveren
            afnemen
            zon - efficientie
        """
        chosen_unit = self.select_unit()
        hor_label = f"{self.period.name if self.period is not None else 'Now: '} [{chosen_unit}]"
        solar = f"{self.solar_value:.2f}" if self.solar_value is not None else '-'
        prod = f"{self.grid_3phases.current_production:.2f}" if self.grid_3phases is not None else '-'
        cons = f"{self.grid_3phases.current_usage:.2f}" if self.grid_3phases is not None else '-'
        eff = f"{self.solar_efficiency:.2f}" if self.solar_efficiency is not None else '-'
        return f"{hor_label:<12} {solar:<12} {prod:<12} {cons:<12} {eff:<12}"

    def select_unit(self) -> Unit | None:
        if self.grid_3phases is None or self.solar_value is None or self.solar_unit is None:
            return None
        if self.grid_3phases.current_usage is None or self.grid_3phases.current_production is None or self.grid_3phases.unit is None:
            return None
        values: list[tuple[float, Unit]] = [(self.solar_value, self.solar_unit),
                                            (self.grid_3phases.current_production, self.grid_3phases.unit),
                                            (self.grid_3phases.current_usage, self.grid_3phases.unit)]
        converted: list[tuple[float, Unit]] = UnitHandler.convert_common(values)
        # assert converted[0][1] == converted[1][1] == converted[2][1]
        self.solar_value = converted[0][0]
        self.solar_unit = converted[0][1]
        self.grid_3phases = Grid3phases(current_production=converted[1][0],
                                        current_usage=converted[2][0],
                                        unit=converted[1][1])
        return converted[0][1]

    @staticmethod
    def header() -> str:  # TODO later weghalen
        return f"{'':<12} {'Zon':<12} {'Productie':<12} {'Consumptie':<12} {'Efficiency':<12}"

    @staticmethod
    def get_labels() -> list[str]:
        return [
            'Zon',
            'Productie',
            'Consumptie',
            'Efficiency'
        ]

    def get_values_unit(self) -> tuple[list[float | None], Unit | None]:
        chosen_unit = self.select_unit()
        res = [self.solar_value]
        if self.grid_3phases:
            res.append(self.grid_3phases.current_production)
            res.append(self.grid_3phases.current_usage)
        else:
            res.append(None)
            res.append(None)
        res.append(self.solar_efficiency)
        return res, chosen_unit

    @property
    def solar_efficiency(self) -> float | None:
        if self.grid_3phases is None or self.solar_value is None or self.solar_unit is None:
            return None
        if (prod := self.grid_3phases.net_production) is None:
            return None
        try:
            solar_conv = UnitHandler.convert(self.solar_value, self.solar_unit, Unit(self.grid_3phases.unit))
            return (solar_conv - prod) / solar_conv
        except ZeroDivisionError:
            return None
