from enum import Enum, auto


class JobTrigger(Enum):
    PERIODIC = auto()
    CRON = auto()


class CronPeriodicity(Enum):
    DAILY = auto()
    MONTHLY = auto()
    YEARLY = auto()
