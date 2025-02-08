from datetime import timedelta

from celery.schedules import crontab, schedule
from constance import config


class DynamicCrontabBase(crontab):
    def __init__(self, *args, **kwargs):
        self.config_time_key = kwargs.pop("config_time_key", None)
        self.default_hour = kwargs.pop("default_hour", 8)
        self.default_minute = kwargs.pop("default_minute", 0)
        super().__init__(*args, **kwargs)

    def is_due(self, last_run_at):
        try:
            time_str = getattr(config, self.config_time_key)
            hours, minutes = map(int, time_str.split(":"))
            self.hour = {hours}
            self.minute = {minutes}
        except Exception:
            self.hour = {self.default_hour}
            self.minute = {self.default_minute}
        return super().is_due(last_run_at)


class DynamicIntervalBase(schedule):
    def __init__(self, *args, **kwargs):
        self.config_interval_key = kwargs.pop("config_interval_key", None)
        self.default_interval_hours = kwargs.pop("default_interval_hours", 1)
        if not args:
            run_every = kwargs.pop(
                "run_every", timedelta(hours=self.default_interval_hours)
            )
            args = (run_every,)
        super().__init__(*args, **kwargs)

    def update_interval(self):
        try:
            interval_str = getattr(config, self.config_interval_key)
            hours, minutes = map(int, interval_str.split(":"))
            interval_seconds = hours * 3600 + minutes * 60
            self.run_every = timedelta(seconds=interval_seconds)
        except Exception:
            self.run_every = timedelta(hours=self.default_interval_hours)

    def is_due(self, last_run_at):
        self.update_interval()
        return super().is_due(last_run_at)


class EmailCrontabSchedule(DynamicCrontabBase):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("config_time_key", "EMAIL_SEND_TIME")
        kwargs.setdefault("default_hour", 8)
        kwargs.setdefault("default_minute", 0)
        super().__init__(*args, **kwargs)


class WeatherIntervalSchedule(DynamicIntervalBase):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("config_interval_key", "WEATHER_FETCH_INTERVAL")
        kwargs.setdefault("default_interval_hours", 1)
        super().__init__(*args, **kwargs)
