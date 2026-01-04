from datetime import datetime, timedelta
from enum import Enum, auto
from Utils.magic_numbers import (c_MINUTES_PER_HOUR, c_MINUTES_PER_DAY, c_MINUTES_PER_MONTH, c_MINUTES_PER_YEAR,
                                 c_HOURS_PER_DAY, c_SECONDS_PER_MINUTE)


class Period(Enum):
    HOUR = auto()
    DAY = auto()
    MONTH = auto()
    YEAR = auto()
    # de niet-vaste periodes hieronder hebben geen implementatie van to_minutes()
    TODAY = auto()
    THISYEAR = auto()

    def to_minutes(self) -> int:
        if self == self.HOUR:
            return c_MINUTES_PER_HOUR
        elif self == self.DAY:
            return c_MINUTES_PER_DAY
        elif self == self.MONTH:
            return c_MINUTES_PER_MONTH
        elif self == self.YEAR:
            return c_MINUTES_PER_YEAR
        else:
            raise NotImplementedError

    def start_time(self, end_time: datetime | None = None) -> datetime:
        if end_time is None:
            end_time = datetime.now()
        try:
            return end_time - timedelta(minutes=self.to_minutes())
        except NotImplementedError:
            return round_time_on_period(end_time, self, round_up=False)

    def is_contained(self, timerange_secs: float) -> bool:
        try:
            return timerange_secs > self.to_minutes() * c_SECONDS_PER_MINUTE
        except NotImplementedError:
            return timerange_secs > (datetime.now() - self.start_time()).total_seconds()


def time_delay_minutes(time_str: str) -> int | None:
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
        delay += c_MINUTES_PER_HOUR
    if hour is not None:
        if (delay_hours := hour - curr_time.hour) < 0:
            delay_hours += c_HOURS_PER_DAY
        delay += delay_hours * c_MINUTES_PER_HOUR
    return delay


def round_time_on_period(date_time: datetime, period: Period, round_up: bool = True) -> datetime:
    if period == Period.HOUR:
        rounded = datetime(year=date_time.year, month=date_time.month, day=date_time.day, hour=date_time.hour, minute=0, second=0)
        return rounded + timedelta(hours=1) if round_up is True else rounded
    elif period == Period.DAY:
        rounded = datetime(year=date_time.year, month=date_time.month, day=date_time.day, hour=0, minute=0, second=0)
        return rounded + timedelta(days=1) if round_up is True else rounded
    elif period == Period.MONTH:
        if round_up is True:
            try:
                return datetime(year=date_time.year, month=date_time.month + 1, day=1, hour=0, minute=0, second=0)
            except ValueError:
                return datetime(year=date_time.year + 1, month=1, day=1, hour=0, minute=0, second=0)
        else:
            return datetime(year=date_time.year, month=date_time.month, day=1, hour=0, minute=0, second=0)
    elif period == Period.YEAR:
        return datetime(year=date_time.year + 1 if round_up is True else date_time.year, month=1, day=1, hour=0, minute=0, second=0)
    else:
        raise RuntimeError("Unknown Period")


def center_time(date_time: datetime, period: Period) -> datetime:
    return round_time_on_period(date_time, period) - timedelta(minutes=period.to_minutes() / 2)


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
    print(f"Volgend op geheel {period}: {round_time_on_period(datetime.now(), period)}")
    period = Period.DAY
    print(f"Volgend op geheel {period}: {round_time_on_period(datetime.now(), period)}")
    period = Period.MONTH
    print(f"Volgend op geheel {period}: {round_time_on_period(datetime.now(), period)}")
    period = Period.YEAR
    print(f"Volgend op geheel {period}: {round_time_on_period(datetime.now(), period)}")

    period = Period.HOUR
    print(f"2 x volgend op geheel {period}: {round_time_on_period(round_time_on_period(datetime.now(), period), period)}")
    period = Period.DAY
    print(f"2 x volgend op geheel {period}: {round_time_on_period(round_time_on_period(datetime.now(), period), period)}")
    period = Period.MONTH
    print(f"2 x volgend op geheel {period}: {round_time_on_period(round_time_on_period(datetime.now(), period), period)}")
    period = Period.YEAR
    print(f"2 x volgend op geheel {period}: {round_time_on_period(round_time_on_period(datetime.now(), period), period)}")

    period = Period.HOUR
    print(f"Center op geheel {period}: {center_time(datetime.now(), period)}")
    period = Period.DAY
    print(f"Center op geheel {period}: {center_time(datetime.now(), period)}")
    period = Period.MONTH
    print(f"Center op geheel {period}: {center_time(datetime.now(), period)}")
    period = Period.YEAR
    print(f"Center op geheel {period}: {center_time(datetime.now(), period)}")
