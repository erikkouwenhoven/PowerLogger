from __future__ import annotations
from enum import Enum, auto
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
    def get_from_name(name: str) -> P1DataType | None:
        for item in P1DataType:
            if item.name == name:
                return item
        return None

    @staticmethod
    def all_poss():
        return [item for item in list(P1DataType)]


class P1Value:
    """
        Contains one single value (an item of a sample)
    """
    def __init__(self, datatype: P1DataType):
        self.dataType = datatype
        self.value: float | datetime | None = None
        self.unit: bytes | None = None
        self.extra_timestamp: datetime | None = None

    def set_timestamp(self, value: bytes):
        assert self.dataType == P1DataType.TIMESTAMP
        self.value = self.decode_time(value)
        self.unit = None

    def set_value(self, value: float | None, unit: bytes | None = None):
        assert self.dataType != P1DataType.TIMESTAMP
        self.value = value
        self.unit = unit

    def set_extra_timestamp(self, extra: bytes):
        self.extra_timestamp = self.decode_time(extra)

    def get_extra_timestamp(self) -> datetime | None:
        return self.extra_timestamp

    @staticmethod
    def decode_time(value: bytes) -> datetime | None:
        try:
            return datetime.strptime(value.decode()[:12], "%y%m%d%H%M%S")
        except ValueError:
            return None


class P1Sample:
    """
        Contains one sample, i.e. a dict of Values
    """
    def __init__(self, datatypes: list[P1DataType]):
        self.data: dict[P1DataType, P1Value | None] = {datatype: None for datatype in datatypes}

    def add_value(self, value: P1Value):
        self.data[value.dataType] = value

    def get_value(self, datatype: P1DataType) -> P1Value | None:
        return self.data[datatype]

    def get_value_from_name(self, name: str) -> P1Value | None:
        if data_type := P1DataType.get_from_name(name):
            return self.data[data_type]
        return None

    def get_data_types(self) -> list[P1DataType]:
        return [key for key in self.data if key != P1DataType.TIMESTAMP]

    def get_timestamp(self) -> datetime | None:
        try:
            if p1_value := self.data[P1DataType.TIMESTAMP]:
                if value := p1_value.value:
                    assert type(value) == datetime
                    return value
            return None
        except KeyError:
            return None

    def get_extra_value_signals(self) -> list[P1DataType]:
        res = []
        for key in self.data:
            if value := self.data[key]:
                try:
                    if value.get_extra_timestamp() is not None:
                        res.append(key)
                except (AttributeError, IndexError):
                    pass
        return res

    def get_extra_value_signal(self) -> P1DataType | None:
        if extra_signals := self.get_extra_value_signals():
            if len(extra_signals) > 1:
                raise NotImplementedError
            return extra_signals[0]
        return None

    def get_data_types_units(self, signals) -> dict[str, str | None]:
        res: dict[str, str | None] = {}
        for key in self.data:
            if key.name in signals and key != P1DataType.TIMESTAMP:
                if value := self.data[key]:
                    if value.unit is not None:
                        res[key.name] = value.unit.decode('utf-8')
                    else:
                        res[key.name] = None
                else:
                    res[key.name] = None
        return res

    def to_data_item_spec(self, signals: list[str]) -> DataItemSpec:
        result = self.get_data_types_units(signals)
        return DataItemSpec(result)

    def to_data_item(self, p1_signals: list[P1DataType]) -> DataItem | None:
        if (timestamp := self.get_timestamp()) is not None:
            signals = [p1_signal.name for p1_signal in p1_signals]
            data_item = DataItem(self.to_data_item_spec(signals), timestamp=datetime.timestamp(timestamp))
            for element in data_item.data_item_spec.get_elements():
                # unit, idx = data_item.data_item_spec.get_element(element)
                if (value := self.get_value_from_name(element)) is not None:
                    data_item.set_value(element, value.value)
                    # data_item.item_data[idx + 1] = value.value
            return data_item
        return None

    def extra_signal_to_data_item(self, extra_signal: str) -> DataItem | None:
        if extra_value := self.get_value_from_name(extra_signal):
            if timestamp := extra_value.get_extra_timestamp():
                data_item = DataItem(self.to_data_item_spec([extra_signal]), timestamp=datetime.timestamp(timestamp))
                data_item.set_value(str(extra_signal), extra_value.value)
                return data_item
        return None

    def __str__(self) -> str:
        if len(self.data) > 0:
            s = f"{len(self.data)} data items\n"
            for item_type, item_value in self.data.items():
                if item_value is not None:
                    unit_str = item_value.unit if item_value.unit else b""
                    s += f"{item_type}: {item_value.value} {unit_str.decode()}\n"
            return s
        else:
            return ""
