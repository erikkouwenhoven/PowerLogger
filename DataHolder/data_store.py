from DataHolder.buffer_attrs import Persistency, LifeSpan
from DataHolder.storage import Storage


class DataStore:
    """
    Information holder on data store
    """

    def __init__(self, name: str, persistency: Persistency, lifespan: LifeSpan, signals: list[str],
                 sampling_time_minutes: int = None, buf_len: int = 0, db: str = None):
        self.name = name
        self.persistency = persistency
        self.lifespan = lifespan
        self.signals = signals
        self.buf_len = buf_len  # Alleen van toepassing bij circulaire persistency
        self.sampling_time_minutes = sampling_time_minutes  # Alleen van toepassing bij afgeleide data
        self.db = db  # Alleen in geval van persistency
        if self.persistency == Persistency.Persistent:
            assert self.db is not None
        if self.lifespan == LifeSpan.Circular:
            assert self.buf_len > 0
        self.data: Storage | None = None

    def data_store_info(self) -> dict[str, any]:
        return {
            "Name": self.name,
            "Persistency": self.persistency.name,
            "Lifespan": self.lifespan.name,
            "Signals": self.signals,
            "Buf_len": self.buf_len,
            "Db": self.db,
        }
