import logging
from datetime import datetime, timedelta
import copy
from Application.Models.operation import Operation
from Utils.settings import Settings
from P1System.p1_interface import P1Interface
from P1System.data_classes import P1Sample
from SMASystem.sma_interface import SMAInterface, SMADataType
from ZWaveSystem.zwave_interface import ZWaveInterface
from Application.Models.shift_info import ShiftInfo
from DataHolder.data_item import DataItemSpec, DataItem
from DataHolder.data_types import DataType
from DataHolder.data_holder import DataHolder
from DataHolder.storage import Storage
from DataHolder.data_store import DataStore


class Processor:
    """
        Receives and handles events.
    """

    def __init__(self, data_holder: DataHolder):
        self.data_holder = data_holder

    def process_derived_signal(self, sources: list[str], dest: str, operation: Operation, operand: str):
        """
        De signalen van de bron data source worden in bewerkte vorm overgezet naar de destination data source. De tijd
        range waarover dat gebeurt wordt bepaald door wat er al aanwezig is in zowel source als destination. De tijdrange
        die nog ontbreekt in de destination wordt aangevuld tot die in de destionation.

        Is er sprake van meerdere sources dan worden deze gemerged, waarbij de tijdstippen van de eerste source worden
        toegepast op de andere sources door middel van interpolatie.
        De bijwerking gebeurt op basis van de Operation.
        Het bijwerken wordt gedaan van de signalen die in de destination zitten. Er moet dus een counterpart zijn in
        de source. Deze counterpart is ofwel hetzelfde signaal ofwel de operand.

        1. bepaal de signalen die geprocessed moeten worden
        2. bepaal de tijden waarop een waarde moet worden gevonden; twee variaties, vaste sampletijd of samples van de bron
        3. Voer de waardebepaling uit
        4. Opslaan

        MERGE: kopieer de missende en plak een nieuw signal eraan vast door interpolatie
        SHIFT: werk bestaande DataItem bij
        DIFF: maak eem mieuw DataItem
        AVG: maak een nieuw DataItem
        """
        source_signals = [signal for source in sources for signal in self.data_holder.data_store(source).signals]
        dest_signals = [signal for signal in self.data_holder.data_store(dest).signals]
        assert all([dest_signal in source_signals for dest_signal in dest_signals])
        assert operand in source_signals
        assert len(dest_signals) == 1 or operand in dest_signals  # het resultaat van de operatie is ondubbelzinnig

        dest_end_time = self.data_holder.get_timerange(dest)[1]
        src_end_time = min([self.data_holder.get_timerange(source)[1] for source in sources])
        if period := self.data_holder.data_store(dest).sampling_period:
            t_updates = range(dest_end_time + self.data_holder.data_store(dest).sampling_period, src_end_time, period)
        else:
            ref_storage = self.data_holder.data_store(sources[0]).data
            t_updates = ref_storage.timedIndexes(ref_storage.index_from_time(dest_end_time) + 1, None)

        # eerst eens een merge proberen
        operand_data_stores = list(filter(lambda data_store: operand in data_store.signals,
                                          [self.data_holder.data_store(src) for src in sources]))
        assert len(operand_data_stores) == 1
        operand_data_store: DataStore = operand_data_stores[0]

        if len(sources) > 1:  # Merge
            ref_storage = self.data_holder.data_store(sources[0]).data
            i_updates = ref_storage.timedIndexes(ref_storage.index_from_time(dest_end_time) + 1, None)
            for i_update in i_updates:
                data_item = copy.deepcopy(ref_storage.get_data_item(i_update))
                for src in sources[1:]:
                    src_index = self.data_holder.data_store(src).data.index_from_time(datetime.fromtimestamp(data_item.get_timestamp()))
                    data_item.merge(self.data_holder.data_store(src).data.get_data_item(src_index))
                self.data_holder.addMeasurement(dest, data_item)

        # Uitvoeren van operatie in-place
        if operation in (Operation.SHIFT, ):
            ref_storage = self.data_holder.data_store(sources[0]).data  # TODO hier moet je filteren
            i_updates = ref_storage.timedIndexes(ref_storage.index_from_time(dest_end_time) + 1, None)
            for i_update in i_updates:
                data_item = ref_storage.get_data_item(i_update)
                at_time = datetime.fromtimestamp(data_item.get_timestamp())
                if operation == Operation.SHIFT:
                    shifted = self.shift(operand_data_store.data, operand, at_time, -1)
                    data_item.set_value(operand, shifted)

        # Uitvoeren van operatie met aanmaak nieuw DataItem
        if operation in (Operation.AVG, Operation.DIFF):
            ref_storage = self.data_holder.data_store(sources[0]).data
            i_updates = ref_storage.timedIndexes(ref_storage.index_from_time(dest_end_time) + 1, None)
            for i_update in i_updates:
                data_item = ref_storage.get_data_item(i_update)
                at_time = datetime.fromtimestamp(data_item.get_timestamp())
                if operation == Operation.AVG:
                    shifted = self.average()
                    data_item.set_value(operand, shifted)


        for t_update in t_updates:
            self.update(de)

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

    def average(self, storage: Storage, from_time: datetime, to_time: datetime, selected_signals: list[DataType]) -> DataItem:
        data_item_spec = DataItemSpec({signal: self.data_item_spec.get_unit(signal) for signal in selected_signals})
        sample = DataItem(data_item_spec, timestamp=0.5*(datetime.timestamp(from_time) + datetime.timestamp(to_time)))
        logging.debug(f"average: from = {from_time}, to = {to_time}, avg time = {datetime.fromtimestamp(sample.get_timestamp())}")
        for signal in selected_signals:
            cum_sum = 0.0
            cum_count = 0
            for idx in storage.timedIndexes(storage.index_from_time(from_time), storage.index_from_time(to_time)):
                if (value := storage.get_data_item(idx).get_value(signal)) is not None:
                    cum_sum += value
                    cum_count += 1
            try:
                sample.set_value(signal, cum_sum / cum_count)
            except ZeroDivisionError:
                sample.set_value(signal, 0.0)
        return sample

    def differentiate(self, storage: Storage, signal: str, at_time: datetime, diff_time: timedelta) -> float:
        """
        Geeft het verschil van een signaal op een gegeven moment en een delta tijd daarvoor
        :param storage: Storage die de data bevat
        :param signal: Naam van het signaal
        :param at_time: Het moment van bepaling van het signaal
        :param diff_time: tijdsverschil
        :return: Het signaalverschil
        """
        curr = storage.get_data_item(storage.index_from_time(at_time)).get_value(signal)
        prev = storage.get_data_item(storage.index_from_time(at_time) - diff_time).get_value(signal)
        return curr - prev

    def shift(self, storage: Storage, signal: str, at_time: datetime, shift_in_seconds: float) -> float:
        """
        Verschuift het signaal in de tijd t.o.v. het tijdstip in het data-item
        :param storage: Storage die de data bevat
        :param signal: Naam van het signaal
        :param at_time: Het moment van bepaling van het signaal
        :param shift_in_seconds: verschuiving in seconden
        :return: De signaalwaarde op het verschoven tijdstip
        """
        data_item = storage.get_data_item(storage.index_from_time(at_time))
        assert signal in data_item.data_item_spec.get_elements()
        goal_timestamp = data_item.timestamp + shift_in_seconds
        index = storage.index_from_time(datetime.fromtimestamp(goal_timestamp))
        if storage.get_data_item(index).get_timestamp() > goal_timestamp:
            index -= 1
        assert storage.get_data_item(index).get_timestamp() < goal_timestamp < storage.get_data_item(index + 1).get_timestamp()
        float_part = ((goal_timestamp - storage.get_data_item(index).get_timestamp()) /
                      (storage.get_data_item(index + 1).get_timestamp() - storage.get_data_item(index).get_timestamp()))
        interp = ((1 - float_part) * storage.get_data_item(index).get_value(signal) +
                  float_part * storage.get_data_item(index + 1).get_value(signal))
        return interp

    def get_P1_start_time(self) -> datetime:  # TODO staat hier op een rare plek
        return self.p1_interface.interpreter.start_time

    def get_P1_clock(self):
        p1_sample = self.p1_interface.getSample()
        return p1_sample.get_timestamp()
