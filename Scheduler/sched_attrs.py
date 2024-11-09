from enum import Enum, auto


class JobTrigger(Enum):
    PERIODIC = auto()
    CRON = auto()


class CronPeriodicity(Enum):
    HOURLY = auto()
    DAILY = auto()
    MONTHLY = auto()
    YEARLY = auto()
