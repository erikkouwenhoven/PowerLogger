from enum import Enum, auto


class Persistency(Enum):
    Volatile = auto()
    Persistent = auto()


class LifeSpan(Enum):
    Circular = auto()
    Linear = auto()
