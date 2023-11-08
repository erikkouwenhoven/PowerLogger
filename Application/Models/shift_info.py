from Utils.settings import Settings


class ShiftInfo:
    """
    Information holder for shifting a signal in time
    """

    def __init__(self):
        self.shift_in_seconds: float = Settings().get_shift_in_seconds()
        self.signal_to_shift: str = Settings().get_signal_to_shift()
        self.sampling_time = None

    def shift_in_samples(self) -> float:
        assert self.sampling_time
        return self.shift_in_seconds / self.sampling_time

    def set_sampling_time(self, sampling_time):
        self.sampling_time = sampling_time
