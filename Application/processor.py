from typing import List, Union
import logging
from datetime import datetime, timedelta
from Application.Models.operation import Operation
from DataHolder.data_item import DataItemSpec, DataItem
from DataHolder.data_holder import DataHolder
from DataHolder.storage import Storage
from DataHolder.data_store import DataStore
from Utils.settings import Settings


class Processor:
    """
    Processes data to obtain and store derived data.
    """

    def __init__(self, data_holder: DataHolder):
        self.data_holder = data_holder

    def process_derived_signal(self, sources: List[str], dest: str, operation: Operation, operands: List[str]):
        """
        De signalen van de bron data source worden in bewerkte vorm overgezet naar de destination data source. De tijd
        range waarover dat gebeurt wordt bepaald door wat er al aanwezig is in zowel source als destination. De tijdrange
        die nog ontbreekt in de destination wordt aangevuld tot die in de destination.

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
        DIFF: maak eem nieuw DataItem
        AVG: maak een nieuw DataItem
        """
        logging.info(f"Call process_derived_signal with sources={sources}, dest={dest}, operation={operation}, operands={operands}")
        source_signals = [signal for source in sources for signal in self.data_holder.data_store(source).signals]
        dest_signals = [signal for signal in self.data_holder.data_store(dest).signals]
        # assert all([dest_signal in source_signals for dest_signal in dest_signals])
        if operands == ["*"]:
            operands = source_signals
        assert all([operand in source_signals for operand in operands])
        assert len(dest_signals) == 1 or all([operand in dest_signals for operand in operands])  # het resultaat van de operatie is ondubbelzinnig
        if operation != Operation.AVG:
            assert len(operands) == 1

        dest_end_time = self.data_holder.get_end_time(dest)
        logging.debug(f"dest_end_time = {dest_end_time}")
        try:
            src_end_time = min([self.data_holder.get_end_time(source) for source in sources
                                if self.data_holder.get_end_time(source) is not None])
        except ValueError:
            src_end_time = None

        operand_data_store: DataStore = self.data_holder.data_store(dest)

        if len(sources) > 1:  # Merge
            ref_storage = self.data_holder.data_store(sources[0]).data
            merged_data_item_spec = operand_data_store.data.data_item_spec
            for src in sources:
                merged_data_item_spec.take_over_units(self.data_holder.data_store(src).data.data_item_spec)
            i_updates = ref_storage.timed_indexes(ref_storage.index_from_time(dest_end_time), None,
                                                  skip_first=True)  # Geen dubbelingen bij aansluiting
            for i_update in i_updates:
                time_stamp = ref_storage.get_data_item(i_update).get_timestamp()
                merged_data_item = DataItem(merged_data_item_spec, time_stamp)
                for item in merged_data_item.data_item_spec.get_elements():
                    for src in sources:
                        if item in self.data_holder.data_store(src).data.data_item_spec.get_elements():
                            if src != sources[0]:
                                val = self.data_holder.data_store(src).data.get_interpolated_value(time_stamp, item)
                            else:  # Hier geldt de timestamp van de ref_storage
                                src_data_item = self.data_holder.data_store(src).data.get_data_item(i_update)
                                val = src_data_item.get_value(item)
                            merged_data_item.set_value(item, val)
                operand_data_store.data.add_measurement(merged_data_item)
                logging.info(f"Merged {merged_data_item}")

        # Uitvoeren van operatie door modificatie van bestaand signaal
        if operation in (Operation.SHIFT, ):
            assert len(operands) == 1
            shift_signal = operands[0]
            src_data_stores = list(filter(lambda ds: shift_signal in ds.signals, [self.data_holder.data_store(src) for src in sources]))
            assert len(src_data_stores) == 1
            src_data_store = src_data_stores[0]
            i_updates = operand_data_store.data.timed_indexes(operand_data_store.data.index_from_time(dest_end_time), None)
            for i_update in i_updates:
                if operation == Operation.SHIFT:
                    if data_item := operand_data_store.data.get_data_item(i_update):
                        timestamp = data_item.get_timestamp()
                        shifted = self.shift(src_data_store.data, shift_signal, timestamp, Settings().get_shift_in_seconds())
                        operand_data_store.data.modify(i_update, shift_signal, shifted)
                        # logging.info(f"Modified signal {shift_signal} at {datetime.fromtimestamp(timestamp)} to value {shifted}")

        # Uitvoeren van operatie met aanmaak nieuw DataItem
        elif operation in (Operation.AVG, Operation.SUM, Operation.DIFF, Operation.VALUE):
            assert (period := self.data_holder.data_store(dest).sampling_time_minutes)
            assert len(sources) == 1
            ref_storage = self.data_holder.data_store(sources[0]).data
            at_time = dest_end_time if dest_end_time is not None else datetime.now()
            if operation in (Operation.AVG, Operation.SUM):
                result_data_item = self.average_sum(ref_storage, at_time, at_time + timedelta(minutes=period), operands, avg=True)
            elif operation == Operation.DIFF:
                assert len(operands) == 1
                operand = operands[0]
                assert operand in source_signals
                assert len(dest_signals) == 1
                result_data_item = self.differentiate(ref_storage, operand, dest_signals[0], at_time, timedelta(minutes=period))
            elif operation == Operation.VALUE:
                storage = self.data_holder.data_store(sources[0]).data
                data_item_spec = DataItemSpec({signal: storage.data_item_spec.get_unit(signal) for signal in operands})
                src_data_item = storage.get_data_item(storage.last_index())
                result_data_item = DataItem(data_item_spec, src_data_item.get_timestamp())
                for signal in operands:
                    result_data_item.set_value(signal, src_data_item.get_value(signal))
            else:
                raise NotImplementedError
            logging.debug(f"operation = {operation}; result = {result_data_item}")
            if result_data_item:
                operand_data_store.data.add_measurement(result_data_item)

    @staticmethod
    def average_sum(storage: Storage, from_time: datetime, to_time: datetime, selected_signals: List[str], avg=True) -> DataItem:
        data_item_spec = DataItemSpec({signal: storage.data_item_spec.get_unit(signal) for signal in selected_signals})
        timestamp = 0.5 * (datetime.timestamp(from_time) + datetime.timestamp(to_time)) if avg is True else datetime.timestamp(to_time)
        sample = DataItem(data_item_spec, timestamp=timestamp)
        logging.debug(f"avg/sum: from = {from_time}, to = {to_time}, time = {datetime.fromtimestamp(sample.get_timestamp())}")
        for signal in selected_signals:
            cum_sum = 0.0
            cum_count = 0
            for idx in storage.timed_indexes(storage.index_from_time(from_time), storage.index_from_time(to_time)):
                if (value := storage.get_data_item(idx).get_value(signal)) is not None:
                    cum_sum += value
                    cum_count += 1
            try:
                sample.set_value(signal, cum_sum / cum_count if avg is True else cum_sum)
            except ZeroDivisionError:
                sample.set_value(signal, 0.0)
        return sample

    @staticmethod
    def differentiate(storage: Storage, signal: str, diff_signal: str, at_time: datetime, diff_time: timedelta) -> Union[DataItem, None]:
        """
        Geeft het verschil van een signaal op een gegeven moment en een delta tijd daarvoor
        :param storage: Storage die de data bevat
        :param signal: Naam van het bronsignaal
        :param diff_signal: Naam van het resultaatsignaal
        :param at_time: Het moment van bepaling van het signaal
        :param diff_time: Het tijdsverschil
        :return: Het dataitem met signaalverschil, of None
        """
        logging.debug(f"differentiate: at_time = {at_time}")
        logging.debug(f"differentiate: at_time + diff_time = {at_time + diff_time}")
        if curr_item := storage.get_data_item(storage.index_from_time(at_time)):
            curr = curr_item.get_value(signal)
            logging.debug(f"differentiate: time = {at_time} index = {storage.index_from_time(at_time)} curr = {curr}")
        else:
            logging.debug(f"differentiate: could not assess curr")
            return None
        if new_item := storage.get_data_item(storage.index_from_time(at_time + diff_time)):
            new = new_item.get_value(signal)
            logging.debug(f"differentiate: time = {at_time + diff_time} index = {storage.index_from_time(at_time + diff_time)} new = {new}")
        else:
            logging.debug(f"differentiate: could not assess new")
            return None
        sample = DataItem(DataItemSpec({diff_signal: Settings().get_unit(diff_signal)}), timestamp=at_time.timestamp())
        sample.set_value(diff_signal, new - curr)
        return sample

    @staticmethod
    def shift(storage: Storage, signal: str, at_timestamp: float, shift_in_seconds: float) -> float:
        """
        Verschuift het signaal in de tijd t.o.v. het tijdstip in het data-item
        :param storage: Storage die de data bevat
        :param signal: Naam van het signaal
        :param at_timestamp: Het moment van bepaling van het signaal
        :param shift_in_seconds: verschuiving in seconden
        :return: De signaalwaarde op het verschoven tijdstip
        """
        return storage.get_interpolated_value(at_timestamp + shift_in_seconds, signal)
