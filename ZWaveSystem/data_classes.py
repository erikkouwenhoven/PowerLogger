from __future__ import annotations
from datetime import datetime
from typing import Dict, List, Optional
from openzwave.node import ZWaveNode
from openzwave.value import ZWaveValue
from enum import Enum, auto


class DataTypeZWave(Enum):

    BATTERY_LEVEL = auto()
    RELATIVE_HUMIDITY = auto()
    TEMPERATURE = auto()


    @staticmethod
    def get_from_name(name: str):  # TODO kan ook direct door Enum[naam]
        for item in DataTypeZWave:
            if item.name == name:
                return item

    @staticmethod
    def value_id(data_type: DataTypeZWave):
        return c_values[data_type]

    @staticmethod
    def from_value_id(value_id: int) -> DataTypeZWave:
        for z_type in c_values:
            if c_values[z_type] == value_id:
                return z_type

    def __str__(self):
        return self.name


c_values: Dict[DataTypeZWave, int] = {
    DataTypeZWave.BATTERY_LEVEL: 72057594077773825,
    DataTypeZWave.RELATIVE_HUMIDITY: 72057594076479570,
    DataTypeZWave.TEMPERATURE: 72057594076479506,
}


class ValueZWave:
    """
        Contains one single value (an item of a sample)
    """
    def __init__(self, datatype: DataTypeZWave):
        self.dataType = datatype
        self.value: Optional[float] = None
        self.unit: Optional[str] = None

    def setValue(self, value: float, unit: str = None):
        if value is not None:
            self.value = value
        else:
            self.value = None
        self.unit = unit


class SampleZWave:
    """
        Contains one sample, i.e. a dict of Values
    """
    def __init__(self, node_id: int, datatypes: List[DataTypeZWave]):
        self.timestamp = datetime.timestamp(datetime.now())
        self.node_id = node_id
        self.data: Dict[DataTypeZWave, ValueZWave] = {datatype: None for datatype in datatypes}

    def setValue(self, value: ValueZWave):
        if value.dataType in self.data:
            self.data[value.dataType] = value
        else:
            print(f"SampleZWave.setValue: try to insert {value.dataType}, all I got is {[data_type for data_type in self.data]}")
            raise AssertionError

    def getValue(self, datatype: DataTstrypeZWave) -> float:
        try:
            return self.data[DataTypeZWave[datatype]].value
        except KeyError:
            print(f"getValue: datatype = {datatype} maar ik heb {[key for key in self.data]}")

    def getValueFromName(self, name: str) -> ValueZWave:
        return self.data[DataTypeZWave.get_from_name(name)]

    def get_data_types(self) -> List[DataTypeZWave]:
        return [key for key in self.data]

    def get_timestamp(self) -> float:
        return self.timestamp

    def get_data_types_units(self) -> Dict[str, str]:
        res = {}
        for key in self.data:
            if value := self.data[key]:
                res[key.name] = value.unit
            else:
                res[key.name] = None
        return res

    @classmethod
    def from_zwave_data(cls, z_wave_node: ZWaveNode, z_wave_value: ZWaveValue):
        data_type = DataTypeZWave.from_value_id(z_wave_value.value_id)
        sample = cls(z_wave_node.node_id, [data_type])
        value = ValueZWave(data_type)
        value.setValue(z_wave_value.data, z_wave_value.units)
        sample.setValue(value)
        return sample

    def __str__(self):
        if len(self.data) > 0:
            S = f"timestamp = {datetime.fromtimestamp(self.timestamp)}"
            S += f"{len(self.data)} data items\n"
            for item in self.data:
                if self.data[item]:
                    unitStr = self.data[item].unit if self.data[item].unit else ""
                    S += f"{item}: {self.data[item].value} {unitStr}\n"
            return S
        else:
            return ""
