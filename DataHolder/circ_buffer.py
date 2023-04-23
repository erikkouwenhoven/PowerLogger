from datetime import datetime
import logging
from P1System.data_classes import DataType


class CircularBuffer:
    """
    Circular buffer holding timed data. Data elements are stored in class DataItem.
    Implementation is using a list where the point of next insertion --the head-- is kept up to date.
    Upon construction the number of elements is supplied.
    """

    def __init__(self, num_elems, elems):
        self.data = []
        self.num_elems = num_elems
        self.head = 0  # position in the data array of the next item
        self.data_item_spec = DataItemSpec(elems)

    def min_time_index(self):
        if len(self.data) < self.num_elems:
            return 0
        else:
            return self.head

    def last_index(self):
        return (self.head - 1 + len(self.data)) % len(self.data)

    def get_data_item(self, idx):
        return self.data[idx]

    def append(self, item):
        logging.debug(f"append: item={item}")
        data_item = DataItem.from_p1sample(item, self.data_item_spec)
        self.data_item_spec.check_units(item)
        if len(self.data) < self.num_elems:
            self.data.append(data_item)
        else:
            self.data[self.head] = data_item
        self.head = (self.head + 1) % self.num_elems

    def str_last(self):
        last_index = self.last_index()
        return [f"{last_index}: {str(self.data[last_index])}"]

    def serialize(self):
        logging.debug(f"get: data = {self.data}")
        result = {"timestamp": [self.get_data_item(idx).get_value('timestamp') for idx in self.timedIndexes()]}
        for elem in self.data_item_spec.get_elements():
            result[str(elem)] = [self.get_data_item(idx).get_value(elem) for idx in self.timedIndexes()]
        logging.debug(f"result from get: {result}")
        return result

    def timedIndexes(self):
        """Geeft de indices op tijdsvolgorde terug door middel van een generator"""
        if self.min_time_index() < self.last_index():
            for idx in range(self.min_time_index(), self.last_index() + 1):
                yield idx
        else:
            for idx in range(self.min_time_index(), len(self.data)):
                yield idx
            for idx in range(self.last_index() + 1):
                yield idx

    def dump(self):
        """Returns list of strings"""
        result = [f"Dump of circular buffer",
                  f"Number of items: {len(self.data)}",
                  f"min_time_index = {self.min_time_index()} @ time {self.get_data_item(self.min_time_index()).get_timestamp_str()}",
                  f"last_time_index = {self.last_index()} @ time {self.get_data_item(self.last_index()).get_timestamp_str()}",
                  f"Time range: from {self.get_data_item(self.min_time_index()).get_timestamp_str()} to"
                  f"{self.get_data_item(self.last_index()).get_timestamp_str()}"]
        logging.debug(f"Timed indexes: {[ind for ind in self.timedIndexes()]}")
        result.append("Data:")
        for item in self.data:
            result.append(str(item))
        return result

    def __len__(self):
        return len(self.data)

    def __getitem__(self, time_stamp):
        low_time_stamp = self.data[self.min_time_index()][0]
        hi_time_stamp_index = self.last_index()
        hi_time_stamp = self.data[hi_time_stamp_index][0]
        if low_time_stamp < time_stamp < self.data[hi_time_stamp_index]:
            index = self.min_time_index() + (time_stamp - low_time_stamp)/(hi_time_stamp - low_time_stamp) * \
                    (hi_time_stamp_index - self.min_time_index() + len(self.data) % len(self.data))
            return self.data[index][0]

    def __str__(self):
        return "".join(self.dump())


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

    def check_units(self, p1sample):
        for element in self.elements:
            unit, idx = self.elements[element]
            # take over the unit from the sample
            if (value := p1sample.getValue(element)) is not None:
                if value[1]:  # the unit of the p1sample
                    if self.elements[element][0] is None:  # the unit of self; is it not set yet?
                        self.elements[element] = p1sample.getValue(element)[1], self.elements[element][1]  # take over the unit, maintain the index
                    else:
                        assert self.elements[element][0] == p1sample.getValue(element)[1]

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

    def get_timestamp(self):
        return self.get_value('timestamp')

    def get_timestamp_str(self):
        return datetime.fromtimestamp(self.get_value('timestamp')).strftime("%d-%m-%Y, %H:%M:%S")

    @staticmethod
    def from_p1sample(p1sample, data_item_spec):
        data_item = DataItem(data_item_spec)
        data_item.item_data[0] = p1sample.getValue(DataType.TIMESTAMP)[0].timestamp()
        for element in data_item_spec.get_elements():
            unit, idx = data_item_spec.get_element(element)
            if (value := p1sample.getValue(element)) is not None:
                data_item.item_data[idx + 1] = value[0]
        return data_item

    def __str__(self):
        S = f"T = {self.get_timestamp_str()}"
        for element in self.data_item_spec.get_elements():
            unit, idx = self.data_item_spec.get_element(element)
            S += f"  {str(element)}: {self.item_data[idx + 1]} {unit}"
        return S
