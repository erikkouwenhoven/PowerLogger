from datetime import datetime, timedelta
import logging
from abc import ABC, ABCMeta, abstractmethod
from DataHolder.db_interface import DBInterface
from DataHolder.data_item import DataItem, DataItemSpec


class Storage(ABC):
    """
    Abstract Base Class for a buffer holding timed data. Data elements are stored in class DataItem.
    """
    def __init__(self, elems: list[str]):
        self.data_item_spec = DataItemSpec({elem: None for elem in elems})

    @abstractmethod
    def min_time_index(self) -> int:
        pass

    @abstractmethod
    def last_index(self, offset: int = 0) -> int | None:
        pass

    @abstractmethod
    def length(self) -> int:
        pass

    @abstractmethod
    def get_data_item(self, idx: int | None) -> DataItem | None:
        pass

    @abstractmethod
    def get_prev_data_item(self, idx: int) -> DataItem | None:
        pass

    @abstractmethod
    def get_next_data_item(self, idx: int) -> DataItem | None:
        pass

    @abstractmethod
    def add_data_item(self, data_item: DataItem):
        pass

    @abstractmethod
    def append(self, data_item: DataItem):
        pass

    @abstractmethod
    def insert(self, data_item: DataItem, idx: int):
        pass

    @abstractmethod
    def modify(self, idx: int, element: str, value: float):
        pass

    @abstractmethod
    def timed_indexes(self, from_index=None, to_index=None):
        pass

    @abstractmethod
    def index_from_time(self, time: datetime) -> int | None:
        pass

    def first_time(self) -> float | None:
        if data_item := self.get_data_item(self.min_time_index()):
            return data_item.get_timestamp()
        else:
            return None

    def last_time(self) -> float | None:
        if data_item := self.get_data_item(self.last_index()):
            return data_item.get_timestamp()
        else:
            return None

    def timestamp_range(self) -> list[float | None]:
        return [self.first_time(), self.last_time()]

    # def serialize(self, signals: list[str] | None = None, human_readable: bool = True) -> dict[str, list[str] | list[float | None] | dict[str, str] | None]:
    def serialize(self, signals: list[str] | None = None, human_readable: bool = True) -> dict[str, list[str] | list[float | None] | dict[str, str | None]]:
        data_items = [self.get_data_item(idx) for idx in self.timed_indexes()]
        timestamps = [data_item.get_timestamp() if data_item else None for data_item in data_items]
        result = {"timestamp": [str(datetime.fromtimestamp(timestamp)) if timestamp else "" for timestamp in timestamps] if human_readable else timestamps,
                  "units": {str(data_type): self.data_item_spec.get_unit(data_type) for data_type in self.data_item_spec.get_elements()}}
        if signals is None:
            signals = self.data_item_spec.get_elements()
        for signal in signals:
            result[signal] = [data_item.get_value(signal) if data_item else None for data_item in data_items]
        # result["units"] = {str(data_type): self.data_item_spec.get_unit(data_type) for data_type in self.data_item_spec.get_elements()}
        return result

    def add_measurement(self, data_item: DataItem, no_zeros: bool = False, min_time_spacing=None):
        if no_zeros is True and data_item.is_zero() is True:
            return
        if min_time_spacing is not None:
            if (timestamp := data_item.get_timestamp()) and (last_timestamp := self.last_time()):
                if (datetime.fromtimestamp(timestamp) - datetime.fromtimestamp(last_timestamp)).total_seconds() < min_time_spacing:
                    return
        self.add_data_item(data_item)

    def get_interpolated_value(self, at_timestamp: float, signal: str) -> float | None:
        if index := self.index_from_time(datetime.fromtimestamp(at_timestamp)):
            if (data_item := self.get_data_item(index)) and (curr_timestamp := data_item.get_timestamp()):
                if curr_timestamp > at_timestamp:
                    next_data_item: DataItem | None = data_item
                    next_timestamp: float | None = curr_timestamp
                    if data_item := self.get_prev_data_item(index):
                        curr_timestamp = data_item.get_timestamp()
                    else:
                        return None
                else:
                    if next_data_item := self.get_next_data_item(index):
                        next_timestamp = next_data_item.get_timestamp()
                    else:
                        return None
                if data_item and next_data_item and curr_timestamp and next_timestamp:
                    if curr_timestamp < at_timestamp < next_timestamp:
                        float_part = ((at_timestamp - curr_timestamp) / (next_timestamp - curr_timestamp))
                        if curr_val := data_item.get_value(signal):
                            if next_val := next_data_item.get_value(signal):
                                return (1.0 - float_part) * curr_val + float_part * next_val
                    else:
                        print(f"PANIC! interpolation at {at_timestamp}, brackets {curr_timestamp, next_timestamp}")
        return None

    def dump(self) -> list[str]:
        if data_item := self.get_data_item(self.min_time_index()):
            first_time_str = data_item.get_timestamp_str()
        else:
            first_time_str = "--"
        if data_item := self.get_data_item(self.last_index()):
            last_time_str = data_item.get_timestamp_str()
        else:
            last_time_str = "--"
        result = [f"Dump of circular buffer",
                  f"Number of items: {self.length()}",
                  f"min_time_index = {self.min_time_index()} @ time {first_time_str}",
                  f"last_time_index = {self.last_index()} @ time {last_time_str}",
                  f"Time range: from {first_time_str} to {last_time_str}"]
        logging.debug(f"Timed indexes: {[ind for ind in self.timed_indexes()]}")
        # result.append(f"Data: {self.serialize()}")
        return result

    def __str__(self) -> str:
        return "".join(self.dump())


class CircularStorage(Storage, metaclass=ABCMeta):
    """
    Abstract Base Class for a circular buffer holding timed data.
    Upon construction the achievable number of elements is supplied. The point of next insertion --the head-- is
    kept up to date.
    """

    def __init__(self, num_elems: int, elems: list[str]):
        Storage.__init__(self, elems)
        self.num_elems = num_elems  # het aantal elementen gealloceerd voor de data
        self.head = self.init_head_from_data()  # position in the data array of the next item

    def min_time_index(self) -> int:
        if self.length() < self.num_elems:
            return 0
        else:
            return self.head

    def last_index(self, offset: int = 0) -> int | None:
        if self.length() > offset:
            return (self.head - offset - 1 + self.length()) % self.length()
        else:
            return None

    def add_data_item(self, data_item: DataItem):
        self.data_item_spec.take_over_units(data_item.data_item_spec)
        logging.debug(f"add_data_item: item={data_item}")
        if self.length() < self.num_elems:
            self.append(data_item)
        else:
            self.insert(data_item, self.head)
        self.head = (self.head + 1) % self.num_elems

    def timed_indexes(self, from_index=None, to_index=None):
        """Geeft de indices op tijdsvolgorde terug door middel van een generator"""
        if from_index is None:
            from_index = self.min_time_index()
        if to_index is None:
            to_index = self.last_index()
        if from_index is not None and to_index is not None:
            if from_index <= to_index:
                for idx in range(from_index, to_index + 1):
                    yield idx
            else:
                for idx in range(from_index, self.length()):
                    yield idx
                for idx in range(to_index + 1):
                    yield idx

    def index_from_time(self, time: datetime) -> int | None:
        if time is None:
            return None
        timestamp = time.timestamp()
        if (lo := self.min_time_index()) is None:
            return None
        if (hi := self.last_index()) is None:
            return None
        if (lo_item := self.get_data_item(lo)) is None or (hi_item := self.get_data_item(hi)) is None:
            return None
        if (lo_timestamp := lo_item.get_timestamp()) is None or (hi_timestamp := hi_item.get_timestamp()) is None:
            return None
        if not lo_timestamp < timestamp < hi_timestamp:
            return None
        iteration = 0
        while lo != hi:
            iteration += 1
            if iteration % 1000 == 0:
                logging.debug(f"iter = {iteration}")
            m = (int((hi - lo) % self.length() / 2) + lo) % self.length()
            if (curr_item := self.get_data_item(m)) is None or (curr_value := curr_item.get_timestamp()) is None:
                return None
            if curr_value < timestamp:
                if lo == m:
                    return lo if timestamp - lo_timestamp < hi_timestamp - timestamp else hi
                lo = m
                lo_timestamp = curr_value
            elif curr_value > timestamp:
                if hi == m:
                    return lo if timestamp - lo_timestamp < hi_timestamp - timestamp else hi
                hi = m
                hi_timestamp = curr_value
            elif curr_value == timestamp:
                return m
            else:
                logging.debug(f"Erroneous exit: lo={lo} hi={hi} timestamp={timestamp}")
                return m
            if abs(hi - lo) <= 1:
                return lo if timestamp - lo_timestamp < hi_timestamp - timestamp else hi
        return None

    def transition_index(self) -> int | None:
        assert self.length() == self.num_elems
        lo = 0
        hi = self.num_elems - 1
        if (lo_item := self.get_data_item(lo)) is None or (hi_item := self.get_data_item(hi)) is None:
            return None
        if (lo_timestamp := lo_item.get_timestamp()) is None or (hi_timestamp := hi_item.get_timestamp()) is None:
            return None
        if lo_timestamp < hi_timestamp:
            return lo
        iteration = 0
        while lo != hi:
            iteration += 1
            if iteration % 1000 == 0:
                logging.debug(f"iter = {iteration}")
                return 0
            m = int((hi + lo) / 2)
            if (curr_item := self.get_data_item(m)) is None or (curr_value := curr_item.get_timestamp()) is None:
                return None
            if curr_value < lo_timestamp:
                hi = m
            else:
                lo = m
            if hi == lo + 1:
                return hi
        return None

    def get_prev_data_item(self, idx: int) -> DataItem | None:
        return self.get_data_item((idx - 1 + self.length()) % self.length())

    def get_next_data_item(self, idx: int) -> DataItem | None:
        return self.get_data_item((idx + 1) % self.length())

    def dump(self) -> list[str]:
        result = [f"Dump of circular buffer",
                  f"Number of items: {self.length()}",
                  f"min_time_index = {self.min_time_index()} @ time {data_item.get_timestamp_str() if (data_item := self.get_data_item(self.min_time_index())) else "-"}",
                  f"last_time_index = {self.last_index()} @ time {data_item.get_timestamp_str() if (data_item := self.get_data_item(self.last_index())) else "-"}",
                  f"Time range: from {data_item.get_timestamp_str() if (data_item := self.get_data_item(self.min_time_index())) else "-"}",
                  f"to {data_item.get_timestamp_str() if (data_item := self.get_data_item(self.last_index())) else "-"}"]
        logging.debug(f"Timed indexes: {[ind for ind in self.timed_indexes()]}")
        result.append(f"Data: {self.serialize()}")
        return result

    def __str__(self) -> str:
        return "".join(self.dump())

    def init_head_from_data(self) -> int:
        head = 0
        if 0 < self.length() < self.num_elems:
            head = self.length()
        else:
            try:
                if (first_item := self.get_data_item(0)) is None:
                    return head
                if (prev_time := first_item.get_timestamp()) is None:
                    return head
            except AttributeError:  # no data
                return head
            for idx in range(self.length()):
                if next_item := self.get_data_item(idx + 1):
                    if next_time := next_item.get_timestamp():
                        if next_time < prev_time:
                            head = idx + 1
                        prev_time = next_time
        return head


class LinearStorage(Storage, metaclass=ABCMeta):
    """
    Abstract Base Class for a linear buffer holding timed data, with no end.
    """

    def __init__(self, elems: list[str]):
        Storage.__init__(self, elems)

    def min_time_index(self) -> int:
        return 0

    def last_index(self, offset: int = 0) -> int | None:
        if self.length() > offset:
            return self.length() - offset - 1
        return None

    def add_data_item(self, data_item: DataItem):
        self.data_item_spec.take_over_units(data_item.data_item_spec)
        logging.debug(f"add_data_item: item={data_item}")
        self.append(data_item)

    def timed_indexes(self, from_index=None, to_index=None):
        """Geeft de indices op tijdsvolgorde terug door middel van een generator"""
        if from_index is None:
            from_index = self.min_time_index()
        if to_index is None:
            to_index = self.last_index()
        for idx in range(from_index, to_index + 1):
            yield idx

    def index_from_time(self, time: datetime) -> int | None:
        if time is None:
            return None
        timestamp = time.timestamp()
        if (lo := self.min_time_index()) is None:
            return None
        if (hi := self.last_index()) is None:
            return None
        if (lo_item := self.get_data_item(lo)) is None or (hi_item := self.get_data_item(hi)) is None:
            return None
        if (lo_timestamp := lo_item.get_timestamp()) is None or (hi_timestamp := hi_item.get_timestamp()) is None:
            return None
        if not lo_timestamp < timestamp < hi_timestamp:
            return None
        while lo != hi:
            m = int((lo + hi) / 2)
            if (curr_item := self.get_data_item(m)) is None or (curr_value := curr_item.get_timestamp()) is None:
                return None
            if curr_value < timestamp:
                lo = m
                lo_timestamp = curr_value
            elif curr_value > timestamp:
                hi = m
                hi_timestamp = curr_value
            elif curr_value == timestamp:
                return m
            if hi - lo <= 1:
                return lo if timestamp - lo_timestamp < hi_timestamp - timestamp else hi
        return None

    def get_prev_data_item(self, idx: int) -> DataItem | None:
        if idx > 0:
            return self.get_data_item(idx - 1)
        return None

    def get_next_data_item(self, idx: int) -> DataItem | None:
        if last_idx := self.last_index():
            if idx < last_idx:
                return self.get_data_item(last_idx + 1)
        return None


class MemStorage(Storage, metaclass=ABCMeta):

    def __init__(self, elems: list[str]):
        super().__init__(elems)
        self.data: list[DataItem] = []

    def length(self) -> int:
        return len(self.data)

    def get_data_item(self, idx: int | None) -> DataItem | None:
        if idx:
            try:
                return self.data[idx]
            except (IndexError, TypeError):
                return None
        return None

    def append(self, data_item: DataItem):
        self.data.append(data_item)

    def insert(self, data_item: DataItem, idx: int):
        self.data[idx] = data_item

    def modify(self, idx: int, element: str, value: float):
        self.data[idx].set_value(element, value)


class PersistentStorage(Storage, metaclass=ABCMeta):

    def __init__(self, elems: list[str], db_interface: DBInterface, table: str):
        super().__init__(elems)
        self.db_interface = db_interface
        self.table = table

    def length(self) -> int:
        return self.db_interface.get_count(self.table)

    def get_data_item(self, idx: int | None) -> DataItem | None:
        if idx is not None:
            res_array = self.db_interface.get_data_items(self.table, idx, self.data_item_spec.get_elements())
            return DataItem.from_array(res_array, self.data_item_spec)
        return None

    def append(self, data_item: DataItem):
        array = data_item.to_array()
        self.db_interface.append_data_item(self.table, self.data_item_spec, array)

    def insert(self, data_item: DataItem, idx: int):
        array = data_item.to_array()
        self.db_interface.insert_data_item(self.table, idx, self.data_item_spec, array)

    def modify(self, idx: int, element: str, value: float):
        self.db_interface.modify_element(self.table, idx, element, value)

    def serialize(self, signals: list[str] | None = None, human_readable: bool = True) -> dict[str, list[str] | list[float | None] | dict[str, str | None]]:
    # def serialize(self, signals: list[str] | None = None, human_readable: bool = True) -> dict:  # override as element-wise data retrieval would be too slow in database implementation
        logging.debug(f"PersistentStorage.serialize: signals = {signals}, human_readable = {human_readable}")
        all_data = self.db_interface.get_all_data(self.table)
        serialized: dict[str, list[str] | list[float | None] | dict[str, str | None]] = \
            {"timestamp": [str(datetime.fromtimestamp(all_data["timestamp"][idx])) if human_readable is True else all_data["timestamp"][idx] for idx in self.timed_indexes()],
             "units": {str(data_type): self.data_item_spec.get_unit(data_type) for data_type in self.data_item_spec.get_elements()}}
        if signals is None:
            signals = [signal for signal in all_data if signal not in ["timestamp", "units"]]
        for signal in signals:
            serialized[signal] = [all_data[signal][idx] for idx in self.timed_indexes()]
        return serialized


class CircularMemStorage(CircularStorage, MemStorage):

    def __init__(self, num_elems: int, elems: list[str]):
        MemStorage.__init__(self, elems)
        CircularStorage.__init__(self, num_elems, elems)


class CircularPersistentStorage(CircularStorage, PersistentStorage):

    def __init__(self, num_elems: int, elems: list[str], db_interface: DBInterface, table: str):
        PersistentStorage.__init__(self, elems=elems, db_interface=db_interface, table=table)
        CircularStorage.__init__(self, num_elems=num_elems, elems=elems)


class LinearPersistentStorage(LinearStorage, PersistentStorage):

    def __init__(self, elems: list[str], db_interface: DBInterface, table: str):
        PersistentStorage.__init__(self, elems=elems, db_interface=db_interface, table=table)
        LinearStorage.__init__(self, elems=elems)


if __name__ == "__main__":
    """Test the binary search"""

    elements = ["A", "B", "C"]
    buf = CircularMemStorage(10, elements)
    start = datetime.now()
    for i in range(13):
        t = start + timedelta(seconds=i)
        item = DataItem(DataItemSpec.from_names(elements), timestamp=datetime.timestamp(t))
        for element in elements:
            item.set_value(element, i)
        buf.add_data_item(item)
    # req = start + timedelta(seconds=-14.2)
    req = start + timedelta(seconds=7.2)
    print(buf)
    if res := buf.index_from_time(req):
        print(f"res = {res} buf = {buf.data[res].get_timestamp()} req={datetime.timestamp(req)}")
    else:
        print(f"Could not find index from time {req}")
    print(f"transition at {buf.transition_index()}")
