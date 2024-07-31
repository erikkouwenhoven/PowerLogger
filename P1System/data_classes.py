from enum import Enum, auto
from typing import List, Dict, Optional, Union
from datetime import datetime
from DataHolder.data_item import DataItemSpec, DataItem


class P1DataType(Enum):

    TIMESTAMP = auto()
    USAGE_TARIFF_1 = auto()
    USAGE_TARIFF_2 = auto()
    PRODUCTION_TARIFF_1 = auto()
    PRODUCTION_TARIFF_2 = auto()
    TARIFF = auto()
    CURRENT_USAGE = auto()
    CURRENT_PRODUCTION = auto()
    CURRENT_USAGE_PHASE1 = auto()
    CURRENT_USAGE_PHASE2 = auto()
    CURRENT_USAGE_PHASE3 = auto()
    CURRENT_PRODUCTION_PHASE1 = auto()
    CURRENT_PRODUCTION_PHASE2 = auto()
    CURRENT_PRODUCTION_PHASE3 = auto()
    CUMULATIVE_GAS = auto()

    def __str__(self):
        return self.name

    @staticmethod
    def get_from_name(name: str):
        for item in P1DataType:
            if item.name == name:
                return item

    @staticmethod
    def all_poss():
        return [item for item in list(P1DataType)]


class P1Value:
    """
        Contains one single value (an item of a sample)
    """
    def __init__(self, datatype: P1DataType):
        self.dataType = datatype
        self.value: Optional[Union[float, datetime]] = None
        self.unit: Optional[bytes] = None
        self.extra_timestamp: Optional[datetime] = None

    def setValue(self, value: Union[float, bytes], unit: bytes = None):
        if value is not None:
            if self.dataType == P1DataType.TIMESTAMP:
                # assert type(value) == bytes
                self.value = self.decode_time(value)
            else:
                # assert type(value) == float
                self.value = value
        else:
            self.value = None
        self.unit = unit

    def set_extra_timestamp(self, extra: bytes):
        self.extra_timestamp = self.decode_time(extra)

    def get_extra_timestamp(self) -> datetime:
        return self.extra_timestamp

    @staticmethod
    def decode_time(value: bytes) -> Optional[datetime]:
        try:
            return datetime.strptime(value.decode()[:12], "%y%m%d%H%M%S")
        except ValueError:
            return None


class P1Sample:
    """
        Contains one sample, i.e. a dict of Values
    """
    def __init__(self, datatypes: List[P1DataType]):
        self.data: Dict[P1DataType, P1Value] = {datatype: None for datatype in datatypes}

    def addValue(self, value: P1Value):
        self.data[value.dataType] = value

    def getValue(self, datatype: P1DataType) -> P1Value:
        return self.data[datatype]

    def getValueFromName(self, name: str) -> P1Value:
        return self.data[P1DataType.get_from_name(name)]

    def get_data_types(self) -> List[P1DataType]:
        return [key for key in self.data if key != P1DataType.TIMESTAMP]

    def get_timestamp(self) -> Optional[datetime]:
        try:
            return self.data[P1DataType.TIMESTAMP].value
        except KeyError:
            return None

    def get_extra_value_signals(self) -> List[P1DataType]:
        res = []
        for key in self.data:
            if value := self.data[key]:
                try:
                    if value.get_extra_timestamp() is not None:
                        res.append(key)
                except (AttributeError, IndexError):
                    pass
        return res

    def get_extra_value_signal(self) -> P1DataType:
        if extra_signals := self.get_extra_value_signals():
            if len(extra_signals) > 1:
                raise NotImplementedError
            return extra_signals[0]

    def get_data_types_units(self, signals) -> Dict[str, str]:
        res = {}
        for key in self.data:
            if key.name in signals and key != P1DataType.TIMESTAMP:
                if value := self.data[key]:
                    res[key.name] = value.unit.decode('utf-8')
                else:
                    res[key.name] = None
        return res

    def to_data_item_spec(self, signals: List[str]) -> DataItemSpec:
        result = self.get_data_types_units(signals)
        return DataItemSpec(result)

    def to_data_item(self, signals: List[str]) -> DataItem:
        if (value := self.getValue(P1DataType.TIMESTAMP)) is not None:
            data_item = DataItem(self.to_data_item_spec(signals), timestamp=datetime.timestamp(value.value))
            for element in data_item.data_item_spec.get_elements():
                unit, idx = data_item.data_item_spec.get_element(element)
                if (value := self.getValueFromName(element)) is not None:
                    data_item.item_data[idx + 1] = value.value
            return data_item

    def extra_signal_to_data_item(self, extra_signal: str):
        if extra_value := self.getValueFromName(extra_signal):
            data_item = DataItem(self.to_data_item_spec([extra_signal]),
                                 timestamp=datetime.timestamp(extra_value.get_extra_timestamp()))
            data_item.set_value(str(extra_signal), self.getValueFromName(extra_signal).value)
            return data_item

    def __str__(self):
        if len(self.data) > 0:
            S = f"{len(self.data)} data items\n"
            for item in self.data:
                if self.data[item]:
                    unitStr = self.data[item].unit if self.data[item].unit else ""
                    S += f"{item}: {self.data[item].value} {unitStr}\n"
            return S
        else:
            return ""
