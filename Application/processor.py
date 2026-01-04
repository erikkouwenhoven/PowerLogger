import logging
from datetime import datetime, timedelta
from itertools import combinations
from Application.Models.operation import Operation
from Application.domain_rules import Grid3phases
from DataHolder.data_item import DataItemSpec, DataItem
from DataHolder.data_holder import DataHolder
from DataHolder.storage import Storage
from DataHolder.data_store import DataStore
from Utils.settings import Settings
from Utils.unit_handling import Unit, UnitHandler
from Utils.time_delay import round_time_on_period, center_time
from Utils.magic_numbers import c_SECONDS_PER_HOUR


class Processor:
    """
    Processes data to obtain and store derived data.
    """

    def __init__(self, data_holder: DataHolder):
        self.data_holder = data_holder

    def process_derived_signal(self, sources: list[str], dest: str, operation: Operation, operands: list[str]):
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
        logging.info(
            f"Call process_derived_signal with sources={sources}, dest={dest}, operation={operation}, operands={operands}")
        source_signals = [signal for source in sources for signal in self.data_holder.data_store(source).signals]
        dest_signals = [signal for signal in self.data_holder.data_store(dest).signals]
        # assert all([dest_signal in source_signals for dest_signal in dest_signals])
        if operands == ["*"]:
            operands = dest_signals
        assert all([operand in source_signals for operand in operands])
        assert len(dest_signals) == 1 or all(
            [operand in source_signals for operand in operands])  # het resultaat van de operatie is ondubbelzinnig

        dest_end_time = self.data_holder.get_end_time(dest)
        logging.debug(f"dest_end_time = {dest_end_time}")
        # try:
        #     src_end_time = min([self.data_holder.get_end_time(source) for source in sources
        #                         if self.data_holder.get_end_time(source) is not None])
        # except ValueError:
        #     src_end_time = None

        operand_data_store: DataStore = self.data_holder.data_store(dest)

        if len(sources) > 1:  # Merge meerdere data sources
            ref_storage = self.data_holder.data_store(sources[0]).data
            merged_data_item_spec = operand_data_store.data.data_item_spec
            for src in sources:
                merged_data_item_spec.take_over_units(self.data_holder.data_store(src).data.data_item_spec)
            for item in merged_data_item_spec.get_elements():
                if item in Settings().derived_signals():
                    dependents = Settings().get_derived_signal_dependency(item)
                    assert len(dependents) > 0
                    dependent = dependents[0]
                    assert dependent in merged_data_item_spec.get_elements()
                    merged_data_item_spec.set_unit(item, merged_data_item_spec.get_unit(dependent))

            i_updates = ref_storage.timed_indexes(ref_storage.index_from_time(dest_end_time), None)
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
                    if item in Settings().derived_signals():
                        merged_data_item.set_value(item, self.derive(item, ref_storage, i_update))  # let op, aanname is dat afgeleide signalen afhangen van signalen in de ref_storage!
                operand_data_store.data.add_measurement(merged_data_item)
                logging.info(f"Merged {merged_data_item}")

        # Uitvoeren van operatie door modificatie van bestaand signaal
        if operation in (Operation.SHIFT,):
            assert len(operands) == 1
            shift_signal = operands[0]
            src_data_stores = list(
                filter(lambda ds: shift_signal in ds.signals, [self.data_holder.data_store(src) for src in sources]))
            assert len(src_data_stores) == 1
            src_data_store = src_data_stores[0]
            i_updates = operand_data_store.data.timed_indexes(operand_data_store.data.index_from_time(dest_end_time),
                                                              None)
            for i_update in i_updates:
                if operation == Operation.SHIFT:
                    if data_item := operand_data_store.data.get_data_item(i_update):
                        timestamp = data_item.get_timestamp()
                        shifted = self.shift(src_data_store.data, shift_signal, timestamp,
                                             Settings().get_shift_in_seconds())
                        operand_data_store.data.modify(i_update, shift_signal, shifted)
                        # logging.info(f"Modified signal {shift_signal} at {datetime.fromtimestamp(timestamp)} to value {shifted}")

        # Uitvoeren van operatie met aanmaak nieuw DataItem
        elif operation in (Operation.AVG, Operation.INTEGRATE, Operation.DIFF, Operation.VALUE):
            assert (period := self.data_holder.data_store(dest).sampling_period)
            assert len(sources) == 1
            ref_storage = self.data_holder.data_store(sources[0]).data
            if operation != Operation.DIFF:
                if (at_time := dest_end_time) is None:
                    at_time = datetime.fromtimestamp(ref_storage.timestamp_range()[0])
            else:
                at_time = center_time(datetime.now(), period)
            if operation in (Operation.AVG, Operation.INTEGRATE):
                assert (ref_period := self.data_holder.data_store(sources[0]).sampling_period)
                start_time = round_time_on_period(at_time, ref_period, round_up = False)
                end_time = round_time_on_period(start_time, period)
                set_time = center_time(start_time, period)
                result_data_item = self.average_integrate(ref_storage, start_time, end_time, set_time, operands,
                                                          avg=operation == Operation.AVG)
            elif operation == Operation.DIFF:
                assert len(operands) == 1
                operand = operands[0]
                assert operand in source_signals
                assert len(dest_signals) == 1
                result_data_item = self.differentiate(ref_storage, operand, dest_signals[0], at_time,
                                                      timedelta(minutes=period.to_minutes()))
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
    def average_integrate(storage: Storage, from_time: datetime, to_time: datetime, set_time: datetime,
                          selected_signals: list[str], avg=True) -> DataItem:
        """
        Bepaalt van een selectie gespecificeerde signalen over een gegeven tijd het gemiddelde of de integraal.
        Het gemiddelde heeft dezelfde eenheid als het oorspronkelijke signaal en is de som van de signaalwaarden over
        het tijdsinterval gedeeld door het aantal waarden.
        De integraal heeft de tijd in uren toegevoegd in zijn eenheid. Uitgaande van equidistante tijdsintervallen is de
        integraal bepaald door de som van de signaalwaarden over het tijdsinterval gedeeld door aantal waarden maal
        lengte van tijdsinterval.
        """
        data_item_spec = DataItemSpec({signal: storage.data_item_spec.get_unit(signal) if avg is True else
                            UnitHandler.integrate(Unit(storage.data_item_spec.get_unit(signal))).value for signal in selected_signals})
        sample = DataItem(data_item_spec, timestamp=datetime.timestamp(set_time))
        hours = (to_time - from_time).total_seconds() / c_SECONDS_PER_HOUR
        for signal in selected_signals:
            cum_sum = 0.0
            cum_count = 0
            for idx in storage.timed_indexes(storage.index_from_time(from_time), storage.index_from_time(to_time)):
                if (value := storage.get_data_item(idx).get_value(signal)) is not None:
                    cum_sum += value
                cum_count += 1
            try:
                factor = cum_count if avg is True else cum_count / hours
                sample.set_value(signal, cum_sum / factor)
            except ZeroDivisionError:
                sample.set_value(signal, 0.0)
        logging.debug(f"{'avg' if avg is True else 'integrate'}: from = {from_time}, to = {to_time}, hours = {hours}, "
                      f"time = {datetime.fromtimestamp(sample.get_timestamp())}, result = {sample}")
        return sample

    @staticmethod
    def differentiate(storage: Storage, signal: str, diff_signal: str, at_time: datetime, diff_time: timedelta) -> \
            DataItem | None:
        """
        Geeft het verschil van een signaal op een gegeven moment en een delta tijd daarvoor
        :param storage: Storage die de data bevat
        :param signal: Naam van het bronsignaal
        :param diff_signal: Naam van het resultaatsignaal
        :param at_time: Het moment van bepaling van het signaal
        :param diff_time: Het tijdsverschil
        :return: Het dataitem met signaalverschil, of None
        """
        to_time = at_time - diff_time
        logging.debug(f"differentiate: to_time = {to_time}")
        if prev_index := storage.index_from_time(to_time):
            if prev_item := storage.get_data_item(prev_index):
                prev = prev_item.get_value(signal)
                logging.debug(f"differentiate: prev_time = {to_time} index = {prev_index} prev = {prev}")
            else:
                logging.debug(f"differentiate: could not assess prev")
                return None
        else:
            prev_item = storage.get_data_item(storage.min_time_index())
            prev = prev_item.get_value(signal)
            logging.debug(f"Using first value at time={datetime.fromtimestamp(storage.first_time())}")

        logging.debug(f"differentiate: at_time = {at_time}")
        if curr_index := storage.index_from_time(at_time):
            if curr_item := storage.get_data_item(curr_index):
                curr = curr_item.get_value(signal)
                logging.debug(f"differentiate: time = {at_time} index = {storage.index_from_time(at_time)} curr = {curr}")
            else:
                logging.debug(f"differentiate: could not assess curr")
                return None
        else:
            curr_item = storage.get_data_item(storage.last_index())
            curr = curr_item.get_value(signal)
            logging.debug(f"Using last value at time={datetime.fromtimestamp(storage.last_time())}")
        sample = DataItem(DataItemSpec({diff_signal: UnitHandler.differentiate(Unit(curr_item.get_unit(signal))).value}),
                          timestamp=to_time.timestamp())
        try:
            sample.set_value(diff_signal, curr - prev)
        except TypeError:  # het is voorgekomen dat new = None, had te maken met het eerder missen van scheduled function
            sample.set_value(diff_signal, None)
        return sample

    @staticmethod
    def shift(storage: Storage, signal: str, at_timestamp: float, shift_in_seconds: float) -> float | None:
        """
        Verschuift het signaal in de tijd t.o.v. het tijdstip in het data-item
        :param storage: Storage die de data bevat
        :param signal: Naam van het signaal
        :param at_timestamp: Het moment van bepaling van het signaal
        :param shift_in_seconds: verschuiving in seconden
        :return: De signaalwaarde op het verschoven tijdstip
        """
        return storage.get_interpolated_value(at_timestamp + shift_in_seconds, signal)

    @staticmethod
    def derive(signal: str, src: Storage, i_update: int) -> float | None:
        dependents = Settings().get_derived_signal_dependency(signal)
        src_data_item = src.get_data_item(i_update)
        values = {signal_name: src_data_item.get_value(signal_name) for signal_name in dependents}
        units = [src_data_item.get_unit(signal_name) for signal_name in dependents]
        for unit1, unit2 in combinations(units, 2):
            assert unit1 == unit2
        assert len(units) > 0
        unit = units[0]
        match signal:
            case "NET_USAGE":
                return Grid3phases(values['CURRENT_USAGE'], values['CURRENT_PRODUCTION'], unit=Unit(unit)).net_consumption
            case "NET_PRODUCTION":
                return Grid3phases(values['CURRENT_USAGE'], values['CURRENT_PRODUCTION'], unit=Unit(unit)).net_production
