import logging
from datetime import datetime, timedelta
from Utils.settings import Settings
from P1System.p1_interface import P1Interface
from P1System.data_classes import P1Sample
from SMASystem.sma_interface import SMAInterface, SMADataType
from ZWaveSystem.zwave_interface import ZWaveInterface
from Application.Models.shift_info import ShiftInfo
from DataHolder.data_holder import DataHolder
from DataHolder.storage import DataItem


class Processor:
    """
        Receives and handles events.
    """

    def __init__(self, data_holder: DataHolder):
        self.data_holder = data_holder

    def transfer_derived_value(self, source: str, dest: str, interval: timedelta, shift_info=None, exclude_signals=("CUMULATIVE_GAS")):
        """
        De signalen van de bron data source worden in bewerkte vorm overgezet naar de destination data source.
        Eventueel wordt het er een verschuiving in de tijd toegepast.
        Er kunnen selectief signalen worden overgeslagen bij de overzetting door deze te benoemen in de exclude_signals
        Van een bron data source naar een destination data source worden de signalen in bewerkte vorm ov
        """
        if (source_timerange := self.data_holder.get_timerange(source)) is not None:
            start_timestamp = datetime.timestamp(datetime.fromtimestamp(source_timerange[1]) - interval)
            end_timestamp = source_timerange[1]
            if start_timestamp < source_timerange[0]:
                start_timestamp = source_timerange[0]

            start_time = datetime.fromtimestamp(start_timestamp)
            end_time = datetime.fromtimestamp(end_timestamp)
            logging.debug(f"Time range for persistent value calculation: {start_time} > {end_time}")
            # shift_info = ShiftInfo()
            # shift_info.set_sampling_time(self.p1_interface.get_sampling_period())
            avg_signals = [signal for signal in self.data_holder.data_store(dest).signals if signal not in exclude_signals]
            derived_data_item = self.data_holder.get_average(source, start_time, end_time, avg_signals, shift_info)  # dit is een data-item
            logging.debug(f"Average: {derived_data_item}")
            self.data_holder.addMeasurement(dest, derived_data_item)

    def get_P1_start_time(self) -> datetime:
        return self.p1_interface.interpreter.start_time

    def get_P1_clock(self):
        p1_sample = self.p1_interface.getSample()
        return p1_sample.get_timestamp()
