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
    def last_index(self, offset: int = 0) -> int:
        pass

    @abstractmethod
    def length(self) -> int:
        pass

    @abstractmethod
    def get_data_item(self, idx: int) -> DataItem:
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
    def timedIndexes(self, from_index=None, to_index=None):
        pass

    @abstractmethod
    def index_from_time(self, time: datetime) -> int:
        pass

    def last_time(self) -> float | None:
        try:
            return self.get_data_item(self.last_index()).get_timestamp()
        except (IndexError, AttributeError, TypeError):
            return None

    def timestamp_range(self) -> list[float] | None:
        try:
            return [self.get_data_item(self.min_time_index()).get_timestamp(),
                    self.get_data_item(self.last_index()).get_timestamp()]
        except AttributeError:
            return None

    def serialize(self, signals: list[str] = None) -> dict:
        result = {"timestamp": [self.get_data_item(idx).get_timestamp() for idx in self.timedIndexes()]}
        if signals is None:
            signals = self.data_item_spec.get_elements()
        for signal in signals:
            result[signal] = [self.get_data_item(idx).get_value(signal) for idx in self.timedIndexes()]
        result["units"] = {str(data_type): self.data_item_spec.get_unit(data_type) for data_type in self.data_item_spec.get_elements()}
        return result

    def addMeasurement(self, data_item: DataItem, no_zeros: bool = False, min_time_spacing=None):
        if no_zeros is True and data_item.is_zero() is True:
            return
        if (min_time_spacing is not None and
                (datetime.fromtimestamp(data_item.timestamp) - datetime.fromtimestamp(
                    self.last_time())).total_seconds() < min_time_spacing):
            return
        self.add_data_item(data_item)

    def dump(self) -> list[str]:
        result = [f"Dump of circular buffer",
                  f"Number of items: {self.length()}",
                  f"min_time_index = {self.min_time_index()} @ time {self.get_data_item(self.min_time_index()).get_timestamp_str()}",
                  f"last_time_index = {self.last_index()} @ time {self.get_data_item(self.last_index()).get_timestamp_str()}",
                  f"Time range: from {self.get_data_item(self.min_time_index()).get_timestamp_str()} to"
                  f"{self.get_data_item(self.last_index()).get_timestamp_str()}"]
        logging.debug(f"Timed indexes: {[ind for ind in self.timedIndexes()]}")
        result.append(f"Data: {self.serialize()}")
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
        self.num_elems = num_elems
        self.head = 0  # position in the data array of the next item

    def min_time_index(self) -> int:
        if self.length() < self.num_elems:
            return 0
        else:
            return self.head

    def last_index(self, offset: int = 0) -> int:
        if self.length() > offset:
            return (self.head - offset - 1 + self.length()) % self.length()

    def add_data_item(self, data_item: DataItem):
        self.data_item_spec.check_units(data_item.data_item_spec)
        logging.debug(f"add_data_item: item={data_item}")
        if self.length() < self.num_elems:
            self.append(data_item)
        else:
            self.insert(data_item, self.head)
        self.head = (self.head + 1) % self.num_elems

    def timedIndexes(self, from_index=None, to_index=None):
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

    def index_from_time(self, time: datetime) -> int:
        timestamp = time.timestamp()
        lo = self.min_time_index()
        hi = self.last_index()
        iteration = 0
        while lo != hi:
            iteration += 1
            if iteration % 1000 == 0:
                logging.debug(f"iter = {iteration}")
            m = (int((hi - lo) % self.length() / 2) + lo) % self.length()
            curr_value = self.get_data_item(m).get_timestamp()
            if curr_value < timestamp:
                if lo == m:
                    return lo if timestamp - self.get_data_item(lo).get_timestamp() < self.get_data_item(hi).get_timestamp() - timestamp else hi
                lo = m
            elif curr_value > timestamp:
                if hi == m:
                    return lo if timestamp - self.get_data_item(lo).get_timestamp() < self.get_data_item(hi).get_timestamp() - timestamp else hi
                hi = m
            elif curr_value == timestamp:
                return m
            else:
                logging.debug(f"Erroneous exit: lo={lo} hi={hi} timestamp={timestamp}")
                return m
            if abs(hi - lo) <= 1:
                return lo if timestamp - self.get_data_item(lo).get_timestamp() < self.get_data_item(hi).get_timestamp() - timestamp else hi

    def dump(self) -> list[str]:
        result = [f"Dump of circular buffer",
                  f"Number of items: {self.length()}",
                  f"min_time_index = {self.min_time_index()} @ time {self.get_data_item(self.min_time_index()).get_timestamp_str()}",
                  f"last_time_index = {self.last_index()} @ time {self.get_data_item(self.last_index()).get_timestamp_str()}",
                  f"Time range: from {self.get_data_item(self.min_time_index()).get_timestamp_str()} to"
                  f"{self.get_data_item(self.last_index()).get_timestamp_str()}"]
        logging.debug(f"Timed indexes: {[ind for ind in self.timedIndexes()]}")
        result.append(f"Data: {self.serialize()}")
        return result

    def __str__(self) -> str:
        return "".join(self.dump())


class LinearStorage(Storage, metaclass=ABCMeta):
    """
    Abstract Base Class for a linear buffer holding timed data, with no end.
    """

    def __init__(self, elems: list[str]):
        Storage.__init__(self, elems)

    def min_time_index(self) -> int:
        return 0

    def last_index(self, offset: int = 0) -> int:
        if self.length() > offset:
            return self.length() - offset - 1

    def add_data_item(self, data_item: DataItem):
        self.data_item_spec.check_units(data_item.data_item_spec)
        logging.debug(f"add_data_item: item={data_item}")
        self.append(data_item)

    def timedIndexes(self, from_index=None, to_index=None):
        """Geeft de indices op tijdsvolgorde terug door middel van een generator"""
        if from_index is None:
            from_index = self.min_time_index()
        if to_index is None:
            to_index = self.last_index()
        for idx in range(from_index, to_index + 1):
            yield idx

    def index_from_time(self, time: datetime) -> int:
        timestamp = time.timestamp()
        lo = self.min_time_index()
        hi = self.last_index()
        while lo != hi:
            m = int((lo + hi) / 2)
            curr_value = self.get_data_item(m).get_timestamp()
            if curr_value < timestamp:
                lo = m
            elif curr_value > timestamp:
                hi = m
            elif curr_value == timestamp:
                return m
            if hi - lo <= 1:
                return lo if timestamp - self.get_data_item(lo).get_timestamp() < self.get_data_item(hi).get_timestamp() - timestamp else hi


class MemStorage(Storage, metaclass=ABCMeta):

    def __init__(self, elems: list[str]):
        super().__init__(elems)
        self.data = []

    def length(self) -> int:
        return len(self.data)

    def get_data_item(self, idx: int) -> DataItem | None:
        try:
            return self.data[idx]
        except IndexError:
            return None

    def append(self, data_item: DataItem):
        self.data.append(data_item)

    def insert(self, data_item: DataItem, idx: int):
        self.data[idx] = data_item


class PersistentStorage(Storage, metaclass=ABCMeta):

    def __init__(self, elems: list[str], db_interface: DBInterface, table: str):
        super().__init__(elems)
        self.db_interface = db_interface
        self.table = table

    def length(self) -> int:
        return self.db_interface.get_count(self.table)

    def get_data_item(self, idx: int) -> DataItem:
        res = self.db_interface.get_data_items(self.table, idx, self.data_item_spec.get_elements())
        return DataItem.from_array(res, self.data_item_spec)

    def append(self, data_item: DataItem):
        array = data_item.to_array(self.data_item_spec)
        self.db_interface.append_data_item(self.table, self.data_item_spec, array)

    def insert(self, data_item: DataItem, idx: int):
        array = data_item.to_array(self.data_item_spec)
        self.db_interface.insert_data_item(self.table, idx, self.data_item_spec, array)

    def serialize(self, signals: list[str] = None) -> dict:  # override as element-wise data retrieval would be too slow in database implementation
        all_data = self.db_interface.get_all_data(self.table)
        res = {}
        for item in all_data:
            if item == "units" or item == "timestamp" or (signals is not None and item in signals):
                res[item] = [all_data[item][idx] for idx in self.timedIndexes()]
        res["units"] = {str(data_type): self.data_item_spec.get_unit(data_type) for data_type in self.data_item_spec.get_elements()}
        return res


class CircularMemStorage(CircularStorage, MemStorage):

    def __init__(self, num_elems: int, elems: list[str]):
        CircularStorage.__init__(self, num_elems, elems)
        MemStorage.__init__(self, elems)


class CircularPersistentStorage(CircularStorage, PersistentStorage):

    def __init__(self, num_elems: int, elems: list[str], db_interface: DBInterface, table: str):
        CircularStorage.__init__(self, num_elems=num_elems, elems=elems)
        PersistentStorage.__init__(self, elems=elems, db_interface=db_interface, table=table)


class LinearPersistentStorage(LinearStorage, PersistentStorage):

    def __init__(self, elems: list[str], db_interface: DBInterface, table: str):
        LinearStorage.__init__(self, elems=elems)
        PersistentStorage.__init__(self, elems=elems, db_interface=db_interface, table=table)


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
    req = start + timedelta(seconds=-14.2)
    res = buf.index_from_time(req)
    print(buf)
    print(f"res = {res} buf = {buf.data[res].timestamp} req={datetime.timestamp(req)}")
