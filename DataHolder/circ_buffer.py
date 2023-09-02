from datetime import datetime
import logging
from abc import ABCMeta, abstractmethod
from DataHolder.db_interface import DBInterface
from DataHolder.data_types import DataType
from DataHolder.data_item import DataItem, DataItemSpec


class CircularStorage(metaclass=ABCMeta):
    """
    Abstract Base Class for a circular buffer holding timed data. Data elements are stored in class DataItem.
    Upon construction the achievable number of elements is supplied. The point of next insertion --the head-- is
    kept up to date.
    """

    def __init__(self, num_elems: int, elems: list[str]):
        self.num_elems = num_elems
        self.head = 0  # position in the data array of the next item
        self.data_item_spec = DataItemSpec({elem: None for elem in elems})

    def min_time_index(self) -> int:
        if self.length() < self.num_elems:
            return 0
        else:
            return self.head

    def last_index(self) -> int:
        try:
            return (self.head - 1 + self.length()) % self.length()
        except ZeroDivisionError:
            if self.head > 0:
                return self.head - 1
            else:
                return 0

    @abstractmethod
    def length(self) -> int:
        pass

    @abstractmethod
    def get_data_item(self, idx: int) -> DataItem:
        pass

    @abstractmethod
    def append(self, data_item: DataItem):
        pass

    @abstractmethod
    def insert(self, data_item: DataItem, idx: int):
        pass

    def add_data_item(self, data_item: DataItem):
        self.data_item_spec.check_units(data_item.data_item_spec)
        logging.debug(f"add_data_item: item={data_item}")
        if self.length() < self.num_elems:
            self.append(data_item)
        else:
            self.insert(data_item, self.head)
        self.head = (self.head + 1) % self.num_elems

    def str_last(self) -> list[str]:
        last_index = self.last_index()
        return [f"{last_index}: {str(self.get_data_item(last_index))}"]

    def last_time(self) -> float:
        return self.get_data_item(self.last_index()).get_timestamp()

    def timestamp_range(self) -> list[float]:
        return [self.get_data_item(self.min_time_index()).get_timestamp(),
                self.get_data_item(self.last_index()).get_timestamp()]

    def serialize(self) -> dict:
        result = {"timestamp": [self.get_data_item(idx).get_timestamp() for idx in self.timedIndexes()]}
        for elem in self.data_item_spec.get_elements():
            result[str(elem)] = [self.get_data_item(idx).get_value(elem) for idx in self.timedIndexes()]
        result["units"] = {str(data_type): self.data_item_spec.get_unit(data_type) for data_type in self.data_item_spec.get_elements()}
        return result

    def timedIndexes(self, from_index=None, to_index=None):
        """Geeft de indices op tijdsvolgorde terug door middel van een generator"""
        if from_index is None:
            from_index = self.min_time_index()
        if to_index is None:
            to_index = self.last_index()
        if from_index < to_index:
            for idx in range(from_index, to_index + 1):
                yield idx
        else:
            for idx in range(from_index, self.length()):
                yield idx
            for idx in range(to_index + 1):
                yield idx

    def average(self, from_time: datetime, to_time: datetime, selected_signals: list[DataType]) -> DataItem:
        sample = DataItem(self.data_item_spec, timestamp=0.5*(datetime.timestamp(from_time) + datetime.timestamp(to_time)))
        logging.debug(f"average: from={from_time} to={to_time}")
        logging.debug(f"avg time = {datetime.fromtimestamp(sample.get_timestamp())}")
        indexes = [idx for idx in self.timedIndexes(self.index_from_time(from_time), self.index_from_time(to_time))]
        for signal in selected_signals:
            assert signal in self.data_item_spec.get_elements()
            cumsum = 0.0
            for idx in indexes:
                if (value := self.get_data_item(idx).get_value(signal)) is not None:
                    cumsum += value
            sample.set_value(signal, cumsum/len(indexes))
        logging.debug(f"averaging count: {len(indexes)}")
        return sample

    def index_from_time(self, time: datetime) -> int:
        timestamp = time.timestamp()
        lo = self.min_time_index()
        hi = self.last_index()
        iter = 0
        while lo != hi:
            iter += 1
            if iter % 1000 == 0:
                logging.debug(f"iter = {iter}")
#            m = int((lo + hi) / 2)
            m = (int((hi - lo) % self.length() / 2) + lo) % self.length()
            curr_value = self.get_data_item(m).get_timestamp()
            if curr_value < timestamp:
                lo = m
            elif curr_value > timestamp:
                hi = m
            elif curr_value == timestamp:
                return m
            if abs(hi - lo) <= 1:
                return lo
        logging.debug(f"Erroneous exit: lo={lo} hi={hi} timestamp={timestamp}")

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


class CircularMemBuf(CircularStorage):

    def __init__(self, num_elems: int, elems: list[str]):
        super().__init__(num_elems, elems)
        self.data = []

    def length(self) -> int:
        return len(self.data)

    def get_data_item(self, idx: int) -> DataItem:
        return self.data[idx]

    def append(self, item: DataItem):
        self.data.append(item)

    def insert(self, item: DataItem, idx: int):
        self.data[idx] = item


class CircularPersistentStorage(CircularStorage):

    def __init__(self, num_elems: int, elems: list[str], db_interface: DBInterface):
        super().__init__(num_elems, elems)
        self.db_interface = db_interface
        self.len = self.length()

    def length(self) -> int:
        return self.db_interface.get_count()

    def get_data_item(self, idx: int) -> DataItem:
        res = self.db_interface.get_data_items(idx, self.data_item_spec.get_elements())
        return DataItem.from_array(res, self.data_item_spec)

    def append(self, item: DataItem):
        logging.debug(f"CircularPersistentStorage.append {item}")
        array = item.to_array(self.data_item_spec)
        self.db_interface.append_data_item(self.data_item_spec, array)

    def insert(self, item: DataItem, idx: int):
        array = item.to_array(self.data_item_spec)
        self.db_interface.insert_data_item(idx, self.data_item_spec, array)

    def serialize(self):  # override as element-wise data retrieval would be too slow in database implementation
        all_data = self.db_interface.get_all_data()
        res = {}
        for item in all_data:
            res[item] = [all_data[item][idx] for idx in self.timedIndexes()]
        res["units"] = {str(data_type): self.data_item_spec.get_unit(data_type) for data_type in self.data_item_spec.get_elements()}
        return res


if __name__ == "__main__":
    """Test the binary search"""
    from datetime import timedelta

    elements = ["A", "B", "C"]
    buf = CircularMemBuf(10, elements)
    start = datetime.now()
    for i in range(10):
        t = start + timedelta(seconds=i)
        item = DataItem(DataItemSpec.from_names(elements), timestamp=datetime.timestamp(t))
        for element in elements:
            item.set_value(element, i)
        buf.add_data_item(item)
    req = start + timedelta(seconds=4)
    res = buf.index_from_time(req)
    print(f"res = {res} buf[res] = {buf.data[res]} req={req}")