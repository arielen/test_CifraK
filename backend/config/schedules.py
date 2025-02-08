from celery.schedules import crontab
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


class EmailCrontabSchedule(DynamicCrontabBase):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("config_time_key", "EMAIL_SEND_TIME")
        kwargs.setdefault("default_hour", 8)
        kwargs.setdefault("default_minute", 0)
        super().__init__(*args, **kwargs)
