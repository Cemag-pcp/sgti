from datetime import datetime, time, timedelta


WORK_START = time(7, 0)
WORK_END = time(17, 0)
WORK_SECONDS_PER_DAY = (
    datetime.combine(datetime.min, WORK_END) - datetime.combine(datetime.min, WORK_START)
).total_seconds()


def business_hours_between(start: datetime, end: datetime) -> float:
    """Return the number of business hours between two datetimes.

    Business days: Monday–Friday, 07:00–17:00 (local time).
    Returns hours as a float rounded to one decimal place.
    """
    if end <= start:
        return 0.0

    def clamp_to_workday(dt: datetime):
        """Return seconds into the workday for dt, clamped to [WORK_START, WORK_END]."""
        t = dt.time().replace(second=0, microsecond=0)
        if t <= WORK_START:
            return 0.0
        if t >= WORK_END:
            return WORK_SECONDS_PER_DAY
        return (
            datetime.combine(dt.date(), t) - datetime.combine(dt.date(), WORK_START)
        ).total_seconds()

    total_seconds = 0.0
    current = start.replace(second=0, microsecond=0)

    while current.date() <= end.date():
        if current.weekday() < 5:  # Monday=0 … Friday=4
            if current.date() == start.date() == end.date():
                # same day: just the slice between start and end
                day_start_secs = clamp_to_workday(start)
                day_end_secs = clamp_to_workday(end)
                total_seconds += max(0.0, day_end_secs - day_start_secs)
            elif current.date() == start.date():
                total_seconds += WORK_SECONDS_PER_DAY - clamp_to_workday(start)
            elif current.date() == end.date():
                total_seconds += clamp_to_workday(end)
            else:
                total_seconds += WORK_SECONDS_PER_DAY

        current = datetime.combine(current.date() + timedelta(days=1), WORK_START)

    return round(total_seconds / 3600, 1)
