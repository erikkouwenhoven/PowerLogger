from datetime import datetime, timedelta
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from Utils.settings import Settings
from Application.processor import Processor


class Scheduler:
    """
    Initializes scheduled events, and receives and handles events.
    """

    c_PERSIST_JOB_ID = 'persist'

    def __init__(self, processor: Processor):
        self.processor = processor
        self.scheduler = BackgroundScheduler(timezone="Europe/Berlin")
        self.initialize(self.scheduler)

    def initialize(self, scheduler: BackgroundScheduler):
        scheduler.add_job(self.do_persist, 'interval', minutes=Settings().persist_interval_minutes(),
                          start_date=datetime.now() + timedelta(minutes=Settings().persist_delay_minutes()),
                          id=self.c_PERSIST_JOB_ID)
        scheduler.start()

    def do_persist(self):
        job = self.scheduler.get_job(job_id=self.c_PERSIST_JOB_ID)
        interval = job.trigger.interval
        self.processor.do_persist(interval)
