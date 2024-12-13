from datetime import datetime, timedelta
from Utils.magic_numbers import c_SECONDS_PER_MINUTE, c_SECONDS_PER_HOUR, c_SECONDS_PER_DAY


date_time_fmt = '%d-%m-%y %H:%M:%S'


def time_ago(time_stamp: float) -> str:
    """
    Weergave van verstreken tijd in grootste significante eenheid, met eventueel de daaropvolgende eenheid
    """
    delta = (datetime.now() - datetime.fromtimestamp(time_stamp)).total_seconds()
    days = delta // c_SECONDS_PER_DAY
    left_over_seconds = delta - days * c_SECONDS_PER_DAY
    hours = left_over_seconds // c_SECONDS_PER_HOUR
    left_over_seconds -= hours * c_SECONDS_PER_HOUR
    minutes = left_over_seconds // c_SECONDS_PER_MINUTE
    left_over_seconds -= minutes * c_SECONDS_PER_MINUTE

    if days:
        return f"{days:.0f}d {hours:.0f}h"
    elif hours:
        return f"{hours:.0f}h {minutes:.0f}m"
    elif minutes:
        return f"{minutes:.0f}m"
    else:
        return f"{left_over_seconds:.0f}s"


if __name__ == "__main__":
    print(f"30 min geleden: {time_ago(datetime.timestamp(datetime.now() - timedelta(minutes=30)))}")
    print(f"90 min geleden: {time_ago(datetime.timestamp(datetime.now() - timedelta(minutes=90)))}")
    print(f"0.3 min geleden: {time_ago(datetime.timestamp(datetime.now() - timedelta(minutes=0.3)))}")
    print(f"10000 min geleden: {time_ago(datetime.timestamp(datetime.now() - timedelta(minutes=10000)))}")
