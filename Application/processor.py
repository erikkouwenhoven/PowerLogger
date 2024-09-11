import logging
from datetime import datetime, timedelta
import copy
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

    def check_job_parameters(self, sources: list[str], dest: str, operation: Operation, operands: list[str]) -> bool:
        for data_store in sources + [dest]:
            if self.data_holder.data_store(data_store) is None:
                logging.error(f"check_job_parameters: Data store {data_store} is unknown")
                return False

        source_signals = [signal for source in sources for signal in self.data_holder.data_store(source).signals]
        dest_signals = [signal for signal in self.data_holder.data_store(dest).signals]
        if all([dest_signal in source_signals for dest_signal in dest_signals]) is False:
            logging.error(f"check_job_parameters: Not all destination signals ({dest_signals}) in source signals ({source_signals})")
            return False

        if operands == ["*"]:
            operands = source_signals
        if all([operand in source_signals for operand in operands]) is False:
            logging.error(f"check_job_parameters: Not all operands ({operands}) in source signals ({source_signals})")
            return False

        if len(dest_signals) == 1 or all([operand in dest_signals for operand in operands]) is False:
            logging.error(f"check_job_parameters: The result signals of the operation are ambiguous: destination: {dest_signals}, operands: {operands}")
            return False

        if operation != Operation.AVG and len(operands) != 1:
            logging.error(f"check_job_parameters: The operation {operation} requires exactly one operand, instead {len(operands)} are found")
            return False

        return True

    def process_derived_signal(self, sources: list[str], dest: str, operation: Operation, operands: list[str]):
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
        if operands == ["*"]:
            operands = source_signals
        assert all([operand in source_signals for operand in operands])
        assert len(dest_signals) == 1 or all([operand in dest_signals for operand in operands])  # het resultaat van de operatie is ondubbelzinnig
        if operation != Operation.AVG:
            assert len(operands) == 1

        dest_end_time = self.data_holder.get_end_time(dest)
        try:
            src_end_time = min([self.data_holder.get_end_time(source) for source in sources
                                if self.data_holder.get_end_time(source) is not None])
        except ValueError:
            src_end_time = None

        operand_data_stores = list(filter(lambda data_store: any(operand in data_store.signals for operand in operands),
                                          [self.data_holder.data_store(src) for src in sources]))
        assert len(operand_data_stores) == 1
        operand_data_store: DataStore = operand_data_stores[0]

        if len(sources) > 1:  # Merge
            ref_storage = self.data_holder.data_store(sources[0]).data
            i_updates = ref_storage.timedIndexes(ref_storage.index_from_time(dest_end_time), None)
            for i_update in i_updates:
                data_item = copy.deepcopy(ref_storage.get_data_item(i_update))
                for src in sources[1:]:
                    src_index = self.data_holder.data_store(src).data.index_from_time(datetime.fromtimestamp(data_item.get_timestamp()))
                    data_item.merge(self.data_holder.data_store(src).data.get_data_item(src_index))
                self.data_holder.data_store(dest).data.addMeasurement(data_item)

        # Uitvoeren van operatie in-place
        if operation in (Operation.SHIFT, ):
            i_updates = operand_data_store.data.timedIndexes(operand_data_store.data.index_from_time(dest_end_time), None)
            for i_update in i_updates:
                data_item = operand_data_store.data.get_data_item(i_update)
                at_time = datetime.fromtimestamp(data_item.get_timestamp())
                if operation == Operation.SHIFT:
                    shifted = self.shift(operand_data_store.data, operands[0], at_time, -1)
                    data_item.set_value(operands[0], shifted)

        # Uitvoeren van operatie met aanmaak nieuw DataItem
        if operation in (Operation.AVG, Operation.DIFF):
            assert (period := self.data_holder.data_store(dest).sampling_period)
            assert len(sources) == 1
            ref_storage = self.data_holder.data_store(sources[0]).data
            at_time = dest_end_time + timedelta(seconds=period)
            assert at_time <= src_end_time
            if operation == Operation.AVG:
                result_data_item = self.average(ref_storage, dest_end_time, at_time, operands)
            elif operation == Operation.DIFF:
                data_item_spec = DataItemSpec({Settings().get_differential_dest_signal(): Settings().get_differential_dest_unit()})
                result_data_item = self.differentiate(ref_storage, operands[0], at_time, timedelta(seconds=-period), data_item_spec)
            else:
                raise NotImplementedError
            self.data_holder.data_store(dest).data.addMeasurement(result_data_item)

    @staticmethod
    def average(storage: Storage, from_time: datetime, to_time: datetime, selected_signals: list[str]) -> DataItem:
        data_item_spec = DataItemSpec({signal: storage.data_item_spec.get_unit(signal) for signal in selected_signals})
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

    @staticmethod
    def differentiate(storage: Storage, signal: str, at_time: datetime, diff_time: timedelta, data_item_spec: DataItemSpec) -> DataItem:
        """
        Geeft het verschil van een signaal op een gegeven moment en een delta tijd daarvoor
        :param storage: Storage die de data bevat
        :param signal: Naam van het bronsignaal
        :param diff_signal: Naam van het resultaatsignaal
        :param at_time: Het moment van bepaling van het signaal
        :param diff_time: Het tijdsverschil
        :return: Het signaalverschil
        """
        sample = DataItem(data_item_spec, timestamp=at_time.timestamp())
        if curr_item := storage.get_data_item(storage.index_from_time(at_time)):
            curr = curr_item.get_value(signal)
        else:
            sample.set_value(signal, 0.0)
            return sample
        if prev_item := storage.get_data_item(storage.index_from_time(at_time - diff_time)):
            prev = prev_item.get_value(signal)
        else:
            sample.set_value(signal, 0.0)
            return sample
        sample.set_value(signal, curr - prev)
        return sample

    @staticmethod
    def shift(storage: Storage, signal: str, at_time: datetime, shift_in_seconds: float) -> float:
        """
        Verschuift het signaal in de tijd t.o.v. het tijdstip in het data-item
        :param storage: Storage die de data bevat
        :param signal: Naam van het signaal
        :param at_time: Het moment van bepaling van het signaal
        :param shift_in_seconds: verschuiving in seconden
        :return: De signaalwaarde op het verschoven tijdstip
        """
        if data_item := storage.get_data_item(storage.index_from_time(at_time)):
            assert signal in data_item.data_item_spec.get_elements()
            goal_timestamp = data_item.timestamp + shift_in_seconds
            index = storage.index_from_time(datetime.fromtimestamp(goal_timestamp))
            if storage.get_data_item(index).get_timestamp() > goal_timestamp:
                index -= 1
            if storage.get_data_item(index).get_timestamp() < goal_timestamp < storage.get_data_item(index + 1).get_timestamp():
                float_part = ((goal_timestamp - storage.get_data_item(index).get_timestamp()) /
                              (storage.get_data_item(index + 1).get_timestamp() - storage.get_data_item(index).get_timestamp()))
                interp = ((1 - float_part) * storage.get_data_item(index).get_value(signal) +
                          float_part * storage.get_data_item(index + 1).get_value(signal))
                return interp
            else:
                print(f"PANIC! interpolation at {goal_timestamp}, brackets {storage.get_data_item(index).get_timestamp(), storage.get_data_item(index + 1).get_timestamp()}")
