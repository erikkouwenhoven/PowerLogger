from __future__ import annotations

import logging
from datetime import datetime


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

    def __init__(self, types_units: dict[str, str | None]):
        """
        types_units is a dict signal name: unit
        Self.elements is a dict with key the signal type, and value the unit and the index in the data array.
        """
        self.elements: dict[str, tuple[str, int]] = {k: (types_units[k], idx) for idx, k in enumerate(types_units)}

    def add_element(self, data_type: str, unit: str):
        n = len(self.elements)
        self.elements[data_type] = (unit, n)

    def set_unit(self, data_type: str, unit: str):
        existing_unit, idx = self.elements[data_type]
        self.elements[data_type] = (unit, idx)

    def get_unit(self, data_type: str) -> str:
        return self.get_element(data_type)[0]

    def get_element_index(self, data_type: str) -> int:
        return self.get_element(data_type)[1]

    def take_over_units(self, other: DataItemSpec):
        """
        Neemt de eenheden over van een andere DataItemSpec, indien niet aanwezig in self
        """
        for data_type in self.elements:
            # take over the unit from the data
            if data_type in other.elements:
                if (other_value := other.get_element(data_type)) is not None:
                    other_unit, other_idx = other_value
                    unit, idx = self.elements[data_type]
                    if other_unit:
                        if unit is None:
                            self.elements[data_type] = other_unit, idx  # take over the unit, maintain the index
                        else:
                            if unit != other_unit:
                                logging.critical(f"PANIC! unit={unit} other_unit={other_unit}")
                            assert unit == other_unit

    def get_elements(self) -> list[str]:
        return [data_type for data_type in self.elements]

    def get_element(self, data_type: str) -> tuple[str, int]:
        try:
            return self.elements[data_type]
        except KeyError:
            raise SystemExit(f"{data_type} not found, only got {self.get_elements()}")

    def datatype_from_name(self, name: str):
        for data_type in self.elements:
            if data_type == name:
                return data_type

    @classmethod
    def from_names(cls, names: list[str]):
        return cls({name: None for name in names})


class DataItem:
    """Data holder for the circular buffer. Basically a list with first element the time stamp."""

    def __init__(self, data_item_spec: DataItemSpec, timestamp: float = None):
        self.data_item_spec: DataItemSpec = data_item_spec
        self.item_data: list[float | None] = [None] * (len(data_item_spec.get_elements()) + 1)
        self.item_data[0] = timestamp

    def get_value(self, element: str) -> float:
        unit, idx = self.data_item_spec.get_element(element)
        return self.item_data[idx + 1]

    def get_value_and_unit(self, element: str) -> str:
        unit, idx = self.data_item_spec.get_element(element)
        return f"{self.item_data[idx + 1]} {unit}"

    def get_unit(self, element: str) -> str:
        unit, _ = self.data_item_spec.get_element(element)
        return unit

    def set_value(self, element: str, value: float | None):
        data_type = self.data_item_spec.datatype_from_name(element)
        unit, idx = self.data_item_spec.get_element(data_type)
        self.item_data[idx + 1] = value

    def add_value(self, element: str, value: float, unit: str):
        self.data_item_spec.add_element(element, unit)
        unit, idx = self.data_item_spec.get_element(element)
        assert idx == len(self.item_data) - 1
        self.item_data.append(value)

    def merge(self, other: DataItem):
        for element in other.data_item_spec.get_elements():
            self.add_value(element, other.get_value(element), other.data_item_spec.get_unit(element))

    def get_timestamp(self) -> float:
        return self.item_data[0]

    def get_timestamp_str(self) -> str | None:
        if self.item_data[0] is not None:
            return datetime.fromtimestamp(self.item_data[0]).strftime("%d-%m-%Y, %H:%M:%S")

    def is_zero(self) -> bool:
        return all([self.item_data[idx] == 0.0 for idx in range(1, len(self.item_data))])

    @classmethod
    def from_array(cls, array: list[float], data_item_spec: DataItemSpec):
        data_item = cls(data_item_spec, timestamp=array[0])
        for i, element in enumerate(data_item_spec.get_elements()):
            unit, idx = data_item_spec.get_element(element)
            if (value := array[i + 1]) is not None:
                data_item.item_data[idx + 1] = value
        return data_item

    def to_array(self, selected_signals: list[str] | None = None) -> list[float | None]:
        signals = self.data_item_spec.get_elements() if selected_signals is None else selected_signals
        array = [None] * (len(signals) + 1)
        array[0] = self.item_data[0]
        for i, element in enumerate(signals):
            unit, idx = self.data_item_spec.get_element(element)
            array[i + 1] = self.item_data[idx + 1]
        return array

    def __str__(self):
        s = f"T = {self.get_timestamp_str()}"
        for element in self.data_item_spec.get_elements():
            unit, idx = self.data_item_spec.get_element(element)
            s += f"  {str(element)}: {self.item_data[idx + 1]} {unit}"
        return s
