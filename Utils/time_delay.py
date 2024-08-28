from datetime import datetime


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
        delay += 60
    if hour:
        if (delay_hours := hour - curr_time.hour) < 0:
            delay_hours += 24
        delay += delay_hours * 60
    return delay


if __name__ == "__main__":
    time_str = ":10"
    print(f"time_str: {time_str}: {time_delay_minutes(time_str)}")
    time_str = "1:10"
    print(f"time_str: {time_str}: {time_delay_minutes(time_str)}")
    time_str = ":54"
    print(f"time_str: {time_str}: {time_delay_minutes(time_str)}")
    time_str = "22:54"
    print(f"time_str: {time_str}: {time_delay_minutes(time_str)}")
    time_str = ":46"
    print(f"time_str: {time_str}: {time_delay_minutes(time_str)}")
    time_str = "18:46"
    print(f"time_str: {time_str}: {time_delay_minutes(time_str)}")
