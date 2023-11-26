from __future__ import annotations
from typing import List, Dict, Optional, Union
from datetime import datetime
from DataHolder.data_types import DataType
from P1System.data_classes import P1Sample, P1DataType
from ZWaveSystem.data_classes import SampleZWave, DataTypeZWave


class DataItemSpec:
    """
    This class is closely related with class DataItem. DataItem holds a reference to DataItemSpec.

    DataItemSpec holds specification of the data in the CircularBuffer. It contains:
        - the timestamp
        - a number of user defined signals
    The user defined signals
        - are specified at construction
        - are associated with an index giving the position in the DataItem
        - are associated with a unit
    """

    def __init__(self, types_units: Dict[Optional[Union[DataType, str]], str]):
        """
        types_units is a dict DataType: unit
        Self.elements is a dict with key the signal type, and value the unit and the index in the data array.
        """
        self.elements: Dict[DataType, tuple[str, int]] = {k: (types_units[k], idx) for idx, k in enumerate(types_units)}

    def add_element(self, data_type: DataType, unit: str):
        n = len(self.elements)
        self.elements[data_type] = (unit, n)

    def set_unit(self, data_type: DataType, unit: str):
        existing_unit, idx = self.elements[data_type]
        self.elements[data_type] = (unit, idx)

    def get_unit(self, data_type: DataType) -> str:
        return self.get_element(data_type)[0]

    def check_units(self, other):
        for data_type in self.elements:
            unit, idx = self.elements[data_type]
            # take over the unit from the data
            if (other_value := other.get_element(data_type)) is not None:
                other_unit, other_idx = other_value
                if other_unit:
                    if unit is None:
                        self.elements[data_type] = other_unit, idx  # take over the unit, maintain the index
                    else:
                        assert unit == other_unit

    def get_elements(self) -> List[DataType]:
        return [data_type for data_type in self.elements]

    def get_element(self, data_type: DataType) -> tuple[str, int]:
        try:
            return self.elements[data_type]
        except KeyError:
            raise SystemExit(f"{data_type} not found, only got {self.get_elements()}")

    def datatype_from_name(self, name: str):
        for data_type in self.elements:
            if data_type == name:
                return data_type

    @classmethod
    def from_names(cls, names: List[str]):
        return cls({name: None for name in names})

    @classmethod
    def from_p1sample(cls, p1sample: P1Sample, signals: List[str]):
        result = p1sample.get_data_types_units(signals)
        return cls(result)

    @classmethod
    def from_zwave_sample(cls, sample: SampleZWave):
        result = sample.get_data_types_units()
        return cls(result)


class DataItem:
    """Data holder for the circular buffer. Basically a list with first element the time stamp."""

    def __init__(self, data_item_spec: DataItemSpec, timestamp: float = None):
        self.data_item_spec: DataItemSpec = data_item_spec
        self.timestamp: Optional[float] = timestamp
        self.item_data: List[Optional[float]] = [None] * (len(data_item_spec.get_elements()) + 1)

    def get_value(self, element: DataType) -> float:
        unit, idx = self.data_item_spec.get_element(element)
        return self.item_data[idx + 1]

    def get_value_and_unit(self, element: DataType) -> str:
        unit, idx = self.data_item_spec.get_element(element)
        return f"{self.item_data[idx + 1]} {unit}"

    def set_value(self, element: str, value: float):
        unit, idx = self.data_item_spec.get_element(element)
        self.item_data[idx + 1] = value

    def add_value(self, element: Union[DataType, DataTypeZWave], value: float, unit: str):
        self.data_item_spec.add_element(element, unit)
        unit, idx = self.data_item_spec.get_element(element)
        assert idx == len(self.item_data) - 1
        self.item_data.append(value)

    def merge(self, other: DataItem):
        for element in other.data_item_spec.get_elements():
            self.add_value(element, other.get_value(element), other.data_item_spec.get_unit(element))

    def get_timestamp(self) -> float:
        return self.timestamp

    def get_timestamp_str(self) -> str:
        if self.timestamp is not None:
            return datetime.fromtimestamp(self.timestamp).strftime("%d-%m-%Y, %H:%M:%S")

    @classmethod
    def from_p1sample(cls, p1sample: P1Sample, signals: List[str]):
        if (value := p1sample.getValue(P1DataType.TIMESTAMP)) is not None:
            data_item = cls(DataItemSpec.from_p1sample(p1sample, signals), timestamp=datetime.timestamp(value.value))
            for element in data_item.data_item_spec.get_elements():
                unit, idx = data_item.data_item_spec.get_element(element)
                if (value := p1sample.getValueFromName(element)) is not None:
                    data_item.item_data[idx + 1] = value.value
            return data_item

    @classmethod
    def from_p1sample_extra_timestamp(cls, p1sample: P1Sample, extra_signal: str):
        if extra_value := p1sample.getValueFromName(extra_signal):
            data_item = cls(DataItemSpec.from_p1sample(p1sample, [extra_signal]),
                            timestamp=datetime.timestamp(extra_value.get_extra_timestamp()))
            data_item.set_value(str(extra_signal), p1sample.getValueFromName(extra_signal).value)
            return data_item

    @classmethod
    def from_zwave_sample(cls, sample: SampleZWave):
        data_item = cls(DataItemSpec.from_zwave_sample(sample), timestamp=sample.timestamp)
        data_types_units = sample.get_data_types_units()
        for data_type in data_types_units:
            data_item.set_value(data_type, sample.getValue(data_type))
        return data_item

    @classmethod
    def from_array(cls, array: List[float], data_item_spec: DataItemSpec):
        data_item = cls(data_item_spec, timestamp=array[0])
        for i, element in enumerate(data_item_spec.get_elements()):
            unit, idx = data_item_spec.get_element(element)
            if (value := array[i]) is not None:
                data_item.item_data[idx + 1] = value
        return data_item

    def to_array(self, data_item_spec: DataItemSpec) -> List[Optional[float]]:
        array = [None] * (len(data_item_spec.get_elements()) + 1)
        array[0] = self.timestamp
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
