from enum import Enum, auto
from typing import Optional
from datetime import datetime


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
    USAGE_GAS = auto()

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
        self.value: Optional[float] = None
        self.unit: Optional[str] = None

    def setValue(self, value: float, unit: str = None):
        if value is not None:
            if self.dataType == P1DataType.TIMESTAMP:
                self.value = datetime.strptime(value.decode()[:12], "%y%m%d%H%M%S")
            else:
                self.value = float(value)
        else:
            self.value = None
        self.unit = unit


class P1Sample:
    """
        Contains one sample, i.e. a dict of Values
    """
    def __init__(self, datatypes: list[P1DataType]):
        self.data = {datatypes[i]: None for i in range(len(datatypes))}

    def addValue(self, value: P1Value):
        self.data[value.dataType] = (value.value, value.unit)

    def getValue(self, datatype: P1DataType):
        return self.data[datatype]

    def getValueFromName(self, name: str):
        return self.data[P1DataType.get_from_name(name)]

    def get_data_types(self):
        return [key for key in self.data if key != P1DataType.TIMESTAMP]

    def get_data_types_units(self) -> dict[str, str]:
        res = {}
        for key in self.data:
            if key != P1DataType.TIMESTAMP:
                if value := self.data[key]:
                    unit = value[1].decode() if value[1] else ""
                    res[key.name] = unit
                else:
                    res[key.name] = None
        return res

    def __str__(self):
        if len(self.data) > 0:
            S = f"{len(self.data)} data items\n"
            for item in self.data:
                if self.data[item]:
                    unitStr = self.data[item][1].decode() if self.data[item][1] else ""
                    S += f"{item}: {self.data[item][0]} {unitStr}\n"
            return S
        else:
            return ""
