from abc import ABCMeta, abstractmethod
from datetime import datetime
import logging
from P1System.data_classes import DataType


class CircularStorage(metaclass=ABCMeta):
    """
    Abstract Base Class for a circular buffer holding timed data. Data elements are stored in class DataItem.
    Upon construction the achievable number of elements is supplied. The point of next insertion --the head-- is
    kept up to date.
    """

    def __init__(self, num_elems, elems):
        self.num_elems = num_elems
        self.head = 0  # position in the data array of the next item
        self.data_item_spec = DataItemSpec(elems)

    def min_time_index(self):
        if self.length() < self.num_elems:
            return 0
        else:
            return self.head

    def last_index(self):
        try:
            return (self.head - 1 + self.length()) % self.length()
        except ZeroDivisionError:
            if self.head > 0:
                return self.head - 1
            else:
                return 0

    @abstractmethod
    def length(self):
        pass

    @abstractmethod
    def get_data_item(self, idx):
        pass

    @abstractmethod
    def append(self, data_item):
        pass

    @abstractmethod
    def insert(self, data_item, idx):
        pass

    def add_data_item(self, data_item):
        logging.debug(f"add_data_item: item={data_item}")
        self.data_item_spec.check_units(data_item.data_item_spec)
        if self.length() < self.num_elems:
            self.append(data_item)
        else:
            self.insert(data_item, self.head)
        self.head = (self.head + 1) % self.num_elems

    def str_last(self):
        last_index = self.last_index()
        return [f"{last_index}: {str(self.get_data_item(last_index))}"]

    def last_time(self):
        return self.get_data_item(self.last_index()).get_value('timestamp')

    def timestamp_range(self):
        return [self.get_data_item(self.min_time_index()).get_value('timestamp'),
                self.get_data_item(self.last_index()).get_value('timestamp')]

    def serialize(self):
        result = {"timestamp": [self.get_data_item(idx).get_value('timestamp') for idx in self.timedIndexes()]}
        for elem in self.data_item_spec.get_elements():
            result[str(elem)] = [self.get_data_item(idx).get_value(elem) for idx in self.timedIndexes()]
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

    def average(self, from_time, to_time, selected_signals):
        sample = DataItem(DataItemSpec(selected_signals))
        logging.debug(f"average: from={from_time} to={to_time}")
        logging.debug(f"indices: from={self.index_from_time(from_time)} to={self.index_from_time(to_time)}")
        sample.set_value('timestamp', 0.5*(datetime.timestamp(from_time) + datetime.timestamp(to_time)))
        logging.debug(f"avg time = {datetime.fromtimestamp(sample.get_value('timestamp'))}")
#        sample = P1Sample(selected_signals)
        for signal in selected_signals:
            assert signal in self.data_item_spec.get_elements()
            cumsum = 0.0
            N = 0
            for idx in self.timedIndexes(self.index_from_time(from_time), self.index_from_time(to_time)):
                cumsum += self.get_data_item(idx).get_value(signal)
                N += 1
            logging.debug(f"averaging count: {N}")
#            value = P1Value(signal)
#            value.setValue(cumsum/N)
            sample.set_value(signal, cumsum/N)
        return sample

    def index_from_time(self, time):
        timestamp = time.timestamp()
        lo = self.min_time_index()
        hi = self.last_index()
        logging.debug(f"index_from_time({time, timestamp}) lo: {self.get_data_item(lo).get_value('timestamp')} @ {lo}; hi: {self.get_data_item(hi).get_value('timestamp')} @ {hi}")
        iter = 0
        while lo != hi:
            iter += 1
            if iter % 1000 == 0:
                logging.debug(f"iter = {iter}")
#            m = int((lo + hi) / 2)
            m = (int((hi - lo) % self.length() / 2) + lo) % self.length()
            curr_value = self.get_data_item(m).get_value('timestamp')
            if curr_value < timestamp:
                lo = m
            elif curr_value > timestamp:
                hi = m
            elif curr_value == timestamp:
                return m
            if abs(hi - lo) <= 1:
                return lo
        logging.debug(f"Erroneous exit: lo={lo} hi={hi} timestamp={timestamp}")

    def create_data_item(self):
        data_item = DataItem(self.data_item_spec)
        return data_item

    def dump(self):
        """Returns list of strings"""
        result = [f"Dump of circular buffer",
                  f"Number of items: {self.length()}",
                  f"min_time_index = {self.min_time_index()} @ time {self.get_data_item(self.min_time_index()).get_timestamp_str()}",
                  f"last_time_index = {self.last_index()} @ time {self.get_data_item(self.last_index()).get_timestamp_str()}",
                  f"Time range: from {self.get_data_item(self.min_time_index()).get_timestamp_str()} to"
                  f"{self.get_data_item(self.last_index()).get_timestamp_str()}"]
        logging.debug(f"Timed indexes: {[ind for ind in self.timedIndexes()]}")
        result.append(f"Data: {self.serialize()}")
        return result

    def __str__(self):
        return "".join(self.dump())


class CircularMemBuf(CircularStorage):

    def __init__(self, num_elems, elems):
        super().__init__(num_elems, elems)
        self.data = []

    def length(self):
        return len(self.data)

    def get_data_item(self, idx):
        return self.data[idx]

    def append(self, item):
        self.data.append(item)

    def insert(self, item, idx):
        self.data[idx] = item


class CircularPersistentStorage(CircularStorage):

    def __init__(self, num_elems, elems, db_interface):
        super().__init__(num_elems, elems)
        self.db_interface = db_interface
        self.len = self.length()

    def length(self):
        return self.db_interface.get_count()

    def get_data_item(self, idx):
        res = self.db_interface.get_data_item(idx, self.data_item_spec.get_elements())
        return DataItem.from_array(res, self.data_item_spec)

    def append(self, item):
        logging.debug(f"CircularPersistentStorage.append")
        logging.debug(f"item={item}")
        array = item.to_array(self.data_item_spec)
        logging.debug(f"array={array}")
        self.db_interface.append_data_item(self.data_item_spec, array)

    def insert(self, item, idx):
        array = item.to_array(self.data_item_spec)
        self.db_interface.insert_data_item(idx, self.data_item_spec, array)

    def serialize(self):  # override as element-wise data retrieval would be too slow in database implementation
        all_data =  self.db_interface.get_all_data()
        for item in all_data:
            all_data[item] = [all_data[item][idx] for idx in self.timedIndexes()]
        return all_data


class DataItemSpec:
    """
    Specification of the data in the CircularBuffer. In essence it is just a list containing a timestamp and
    number of user defined signals. At construction the user supplies the types and units of these signals.
    """

    def __init__(self, elements):
        """
        Elements is a list containing the type of the signals.
        Self.elements is a dict with key the signal type, and value the unit and the index in the data array.
        """
        self.elements = {k: (None, idx) for idx, k in enumerate(elements)}  # unit not set yet

    def check_units(self, data_item_spec):
        for element in self.elements:
            unit, idx = self.elements[element]
            # take over the unit from the sample
            if (value := data_item_spec.get_element(element)) is not None:
                if value[1]:  # the unit of the p1sample
                    if self.elements[element][0] is None:  # the unit of self; is it not set yet?
                        self.elements[element] = data_item_spec.get_element(element)[1], self.elements[element][1]  # take over the unit, maintain the index
                    else:
                        assert self.elements[element][0] == data_item_spec.get_element(element)[1]

    def get_elements(self):
        return [element for element in self.elements]

    def get_element(self, element):
        return self.elements[element]


class DataItem:
    """Data holder for the circular buffer. Basically a list with first element the time stamp."""

    def __init__(self, data_item_spec):
        self.data_item_spec = data_item_spec
        self.item_data = [None] * (len(data_item_spec.get_elements()) + 1)

    def get_value(self, element):
        if element == 'timestamp':  # TODO timestamp een constant maken
            return self.item_data[0]
        else:
            unit, idx = self.data_item_spec.get_element(element)
            return self.item_data[idx + 1]

    def set_value(self, element, value):
        if element == 'timestamp':
            self.item_data[0] = value
        else:
            unit, idx = self.data_item_spec.get_element(element)
            self.item_data[idx + 1] = value

    def get_timestamp(self):
        return self.get_value('timestamp')

    def get_timestamp_str(self):
        timestamp = self.get_value('timestamp')
        if timestamp is not None:
            return datetime.fromtimestamp(timestamp).strftime("%d-%m-%Y, %H:%M:%S")

    def from_p1sample(self, p1sample):
        if (value := p1sample.getValue(DataType.TIMESTAMP)) is not None:
            self.item_data[0] = value[0].timestamp()
            for element in self.data_item_spec.get_elements():
                unit, idx = self.data_item_spec.get_element(element)
                if (value := p1sample.getValue(element)) is not None:
                    self.item_data[idx + 1] = value[0]
        return self

    @staticmethod
    def from_array(array, data_item_spec):
        data_item = DataItem(data_item_spec)
        data_item.item_data[0] = array[0]
        for i, element in enumerate(data_item_spec.get_elements()):
            unit, idx = data_item_spec.get_element(element)
            if (value := array[i]) is not None:
                data_item.item_data[idx + 1] = value
        return data_item

    def to_array(self, data_item_spec):
        array = [None] * (len(data_item_spec.get_elements()) + 1)
        array[0] = self.item_data[0]
        for i, element in enumerate(data_item_spec.get_elements()):
            unit, idx = data_item_spec.get_element(element)
            array[i + 1] = self.item_data[idx + 1]
        return array

    def __str__(self):
        S = f"T = {self.get_timestamp_str()}"
        for element in self.data_item_spec.get_elements():
            unit, idx = self.data_item_spec.get_element(element)
            S += f"  {str(element)}: {self.item_data[idx + 1]} {unit}"
        return S


if __name__ == "__main__":
    """Test the binary search"""
    from datetime import timedelta

    elements = ["A", "B", "C"]
    buf = CircularMemBuf(10, elements)
    start = datetime.now()
    for i in range(10):
        t = start + timedelta(seconds=i)
        item = DataItem(DataItemSpec(elements))
        item.set_value('timestamp', datetime.timestamp(t))
        for element in elements:
            item.set_value(element, i)
        buf.add_data_item(item)
    req = start + timedelta(seconds=4)
    res = buf.index_from_time(req)
    print(f"res = {res} buf[res] = {buf.data[res]} req={req}")