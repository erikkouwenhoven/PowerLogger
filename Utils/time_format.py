from datetime import datetime, timedelta


date_time_fmt = '%d-%m-%y %H:%M:%S'


def time_ago(time_stamp: float) -> str:
    delta = int((datetime.now() - datetime.fromtimestamp(time_stamp)).total_seconds())
    days = delta // (24 * 3600)
    hrs = delta // 3600
    mins = delta // 60
    secs = delta % 60
    if days:
        return f"{days} d"
    elif hrs:
        return f"{hrs} h {mins} m"
    elif mins:
        return f"{mins} m"
    else:
        return f"{secs} s"
