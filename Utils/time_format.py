from datetime import datetime


date_time_fmt = '%d-%m-%y %H:%M:%S'


def time_ago(time_stamp: float) -> str:
    delta = datetime.now() - datetime.fromtimestamp(time_stamp)
    days = delta.days
    hrs = delta.min // 60
    mins = delta.min
    secs = delta.seconds
    if days:
        return f"{days} d"
    elif hrs:
        return f"{hrs} h {mins} m"
    elif mins:
        return f"{mins} m"
    else:
        return f"{secs} s"
