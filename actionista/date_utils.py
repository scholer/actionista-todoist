
"""

Module dealing specifically with dates and times.

"""
from dateutil import tz
import dateparser
# import datetime
# import pendulum

DATE_DAY_FMT = '%Y-%m-%d'
ISO_8601_FMT = '%Y-%m-%dT%H:%M:%S'
TODOIST_DATE_FMT = "%a %d %b %Y %H:%M +0000"  # e.g. 'Mon 07 Aug 2006 12:34:56 +0000'. Use xx:xx:59 as "all day" time.
# Todoist date format is similar to RFC2822, except that it doesn't have a comma after the weekday.


def utc_time_to_local(utcdatetime, timezone=None, fmt="datetime"):
    """ Todoist has some serious time issues. All due times are stored and transmitted in UTC time.
    But, "special times", e.g. 23:59:59 to mark "end of day" or "all day", is in *local time*.
    Furthermore, there is e.g. summer vs winter time. So, before daylight saving time,
    "end of day" tasks may be 22:59:59 UTC, but after DST "end of day" may be marked as 21:59:59 UTC
    because both times will be 23:59:59 local time.
    You thus need the date in order to convert times between timezones.
    Libraries to deal with datetime conversions:
        pendulum
        zulu
        dateutil
        datetime

    Examples:
        >>> utcdatetime = "Sat 24 Mar 2018 22:59:59 +0000"
        >>> utc_time_to_local(utcdatetime)
        >>> utcdatetime = "Mon 26 Mar 2018 21:59:59 +0000"
        >>> utc_time_to_local(utcdatetime)
    """
    if timezone is None:
        timezone = tz.tzlocal()
    if isinstance(utcdatetime, str):
        utcdatetime = dateparser.parse(utcdatetime)
    if utcdatetime.tzinfo is None:
        utcdatetime.replace(tzinfo=tz.gettz('UTC'))

    # Convert UTC time to local:
    localdt = utcdatetime.astimezone(timezone)

    if fmt is None or fmt == "datetime":
        return localdt
    elif fmt == "date":
        return localdt.date()
    elif fmt == "time":
        return localdt.time()
    else:
        return localdt.strftime(fmt)


def local_time_to_utc(localtime, timezone=None, fmt="datetime"):
    if timezone is None:
        timezone = tz.tzlocal()
    if isinstance(localtime, str):
        localtime = dateparser.parse(localtime)
    if localtime.tzinfo is None:
        localtime.replace(tzinfo=timezone)

    # Convert local time to UTC:
    utcdatetime = localtime.astimezone(tz.gettz('UTC'))

    if fmt is None or fmt == "datetime":
        return utcdatetime
    elif fmt == "date":
        return utcdatetime.date()
    elif fmt == "time":
        return utcdatetime.time()
    else:
        return utcdatetime.strftime(fmt)


def end_of_day(dt):
    return dt.replace(hour=23, minute=59, second=59)


def start_of_day(dt):
    return dt.replace(hour=0, minute=0, second=0)


def human_date_to_iso(human_date, fmt=ISO_8601_FMT):
    """ Convert natural language / contextual dates, e.g. 'today', to iso date string.
    Note: This is a little bit finicky. For instance, "in 2 weeks" works, but none of the following variations do:
        "in two weeks", "2 weeks from now", "two weeks", "in 2 weeks from now", etc.

    The returned datetime object does not by default have any timezone information,
    so the iso datestring is basically local time.
    """
    dt = dateparser.parse(human_date)
    if dt is None:
        print(f"\nERROR: FAILED to parse human input date {human_date!r}.\n")
        raise ValueError(f"FAILED to parse human input date {human_date!r}.")
    return dt.strftime(fmt)