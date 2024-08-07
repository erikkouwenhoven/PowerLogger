from typing import List, Dict, Optional, Any
from DataHolder.buffer_attrs import Persistency, LifeSpan
from DataHolder.storage import Storage


class DataStore:
    """
    Information holder on data store
    """

    def __init__(self, name: str, persistency: Persistency, lifespan: LifeSpan, signals: List[str], buf_len: int = 0, db: str = None):
        self.name = name
        self.persistency = persistency
        self.lifespan = lifespan
        self.signals = signals
        self.buf_len = buf_len
        self.db = db
        if self.persistency == Persistency.Persistent:
            assert self.db is not None
        if self.lifespan == LifeSpan.Circular:
            assert self.buf_len > 0
        self.data: Optional[Storage] = None

    def data_store_info(self) -> Dict[str, Any]:
        return {
            "Name": self.name,
            "Persistency": self.persistency.name,
            "Lifespan": self.lifespan.name,
            "Signals": self.signals,
            "Buf_len": self.buf_len,
            "Db": self.db,
        }
