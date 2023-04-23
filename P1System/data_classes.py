from enum import Enum, auto
from datetime import datetime


class P1Value:
    """
        Contains one single value (an item of a sample)
    """
    def __init__(self, dataType):
        self.dataType = dataType
        self.value = None
        self.unit = None

    def setValue(self, value, unit=None):
        if value is not None:
            if self.dataType == DataType.TIMESTAMP:
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
    def __init__(self, dataTypes):
        self.data = {dataTypes[i]: None for i in range(len(dataTypes))}

    def addValue(self, value: P1Value):
        self.data[value.dataType] = (value.value, value.unit)

    def getValue(self, data_type):
        # print(f"DEBUG >>> getValue: type name = {type(name)}")
        # print(f"DEBUG >>> getValue: name = {name}, data_keys={self.get_data_types()}")
        # print(f"DEBUG >>> getValue: enum = {DataType[name]}")
        # print(f"DEBUG >>> getValue: val = {self.data[DataType[name]]}")
        return self.data[data_type]

    def get_data_types(self):
        return [key for key in self.data if key != DataType.TIMESTAMP]

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


class DataType(Enum):

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

    SOLAR = auto()

    def __str__(self):
        return self.name

    @staticmethod
    def all_poss():
        return [item for item in list(DataType)]

