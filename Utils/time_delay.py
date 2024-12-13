from datetime import datetime, timedelta
from typing import Union
from enum import Enum, auto
from Utils.magic_numbers import c_MINUTES_PER_HOUR, c_MINUTES_PER_DAY, c_MINUTES_PER_MONTH, c_MINUTES_PER_YEAR


class Period(Enum):
    HOUR = auto()
    DAY = auto()
    MONTH = auto()
    YEAR = auto()

    def to_minutes(self) -> int:
        if self == self.HOUR:
            return c_MINUTES_PER_HOUR
        elif self == self.DAY:
            return c_MINUTES_PER_DAY
        elif self == self.MONTH:
            return c_MINUTES_PER_MONTH
        elif self == self.YEAR:
            return c_MINUTES_PER_YEAR


def time_delay_minutes(time_str: str) -> Union[int, None]:
    """
    Geeft de delay in minuten tot de gegeven tijd is bereikt. De tijd is gespecificeerd in de vorm van hh:mm.
    Het deel hh is optioneel, indien weggelaten wordt er voor het eerstvolgende uur een delay bepaald.
    Geeft de delay in minuten terug.
    """
    hour_str, minute_str = time_str.split(':')
    hour = int(hour_str) if hour_str else None
    minute = int(minute_str)
    curr_time = datetime.now()
    if (delay := minute - curr_time.minute) < 0:
        delay += 60
    if hour is not None:
        if (delay_hours := hour - curr_time.hour) < 0:
            delay_hours += 24
        delay += delay_hours * 60
    return delay


def next_time(date_time: datetime, period: Period) -> datetime:
    if period == Period.HOUR:
        rounded = datetime(year=date_time.year, month=date_time.month, day=date_time.day, hour=date_time.hour, minute=0, second=0)
        return rounded + timedelta(hours=1)
    elif period == Period.DAY:
        rounded = datetime(year=date_time.year, month=date_time.month, day=date_time.day, hour=0, minute=0, second=0)
        return rounded + timedelta(days=1)
    elif period == Period.MONTH:
        try:
            return datetime(year=date_time.year, month=date_time.month + 1, day=1, hour=0, minute=0, second=0)
        except ValueError:
            return datetime(year=date_time.year + 1, month=1, day=1, hour=0, minute=0, second=0)
    elif period == Period.YEAR:
        return datetime(year=date_time.year + 1, month=1, day=1, hour=0, minute=0, second=0)
    else:
        raise RuntimeError("Unknown Period")


def center_time(date_time: datetime, period: Period) -> datetime:
    return next_time(date_time, period) - timedelta(minutes=period.to_minutes() / 2)


if __name__ == "__main__":
    time_str = "00:10"
    print(f"time_str: {time_str}. Dit is over: {time_delay_minutes(time_str)//60};{time_delay_minutes(time_str) % 60}")
    time_str = ":10"
    print(f"time_str: {time_str}. Dit is over: {time_delay_minutes(time_str)//60};{time_delay_minutes(time_str) % 60}")
    time_str = "1:10"
    print(f"time_str: {time_str}. Dit is over: {time_delay_minutes(time_str)//60};{time_delay_minutes(time_str) % 60}")
    time_str = ":54"
    print(f"time_str: {time_str}. Dit is over: {time_delay_minutes(time_str)//60};{time_delay_minutes(time_str) % 60}")
    time_str = "22:54"
    print(f"time_str: {time_str}. Dit is over: {time_delay_minutes(time_str)//60};{time_delay_minutes(time_str) % 60}")
    time_str = ":46"
    print(f"time_str: {time_str}. Dit is over: {time_delay_minutes(time_str)//60};{time_delay_minutes(time_str) % 60}")

    period = Period.HOUR
    print(f"Volgend op geheel {period}: {next_time(datetime.now(), period)}")
    period = Period.DAY
    print(f"Volgend op geheel {period}: {next_time(datetime.now(), period)}")
    period = Period.MONTH
    print(f"Volgend op geheel {period}: {next_time(datetime.now(), period)}")
    period = Period.YEAR
    print(f"Volgend op geheel {period}: {next_time(datetime.now(), period)}")

    period = Period.HOUR
    print(f"2 x volgend op geheel {period}: {next_time(next_time(datetime.now(), period), period)}")
    period = Period.DAY
    print(f"2 x volgend op geheel {period}: {next_time(next_time(datetime.now(), period), period)}")
    period = Period.MONTH
    print(f"2 x volgend op geheel {period}: {next_time(next_time(datetime.now(), period), period)}")
    period = Period.YEAR
    print(f"2 x volgend op geheel {period}: {next_time(next_time(datetime.now(), period), period)}")

    period = Period.HOUR
    print(f"Center op geheel {period}: {center_time(datetime.now(), period)}")
    period = Period.DAY
    print(f"Center op geheel {period}: {center_time(datetime.now(), period)}")
    period = Period.MONTH
    print(f"Center op geheel {period}: {center_time(datetime.now(), period)}")
    period = Period.YEAR
    print(f"Center op geheel {period}: {center_time(datetime.now(), period)}")
