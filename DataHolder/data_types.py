class DataType(str):

    def __init__(self):
        super().__init__()

    @classmethod
    def from_str(cls, S : str):
        data_type = S
        return data_type
