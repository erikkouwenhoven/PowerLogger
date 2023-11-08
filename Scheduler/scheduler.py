from datetime import datetime, timedelta
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from Utils.settings import Settings
from Application.processor import Processor


class Scheduler:
    """
    Initializes scheduled events, and receives and handles events.
    """

    def __init__(self, processor: Processor):
        self.processor = processor
        self.scheduler = BackgroundScheduler(timezone="Europe/Berlin")
        self.initialize(self.scheduler)

    def initialize(self, scheduler: BackgroundScheduler):
        job_ids = Settings().scheduled_jobs()
        for job_id in job_ids:
            sched_job = ScheduledJob(job_id)
            scheduler.add_job(self.exec_job, 'interval', minutes=sched_job.interval_minutes,
                              kwargs={'id': job_id, 'source': sched_job.source, 'dest': sched_job.destination},
                              start_date=datetime.now() + timedelta(minutes=sched_job.start_delay_minutes), id=job_id)
        scheduler.start()

    def exec_job(self, **kwargs):
        job_id = kwargs['id']
        job = self.scheduler.get_job(job_id=job_id)
        interval = job.trigger.interval
        if job_id == "persist":
            self.processor.transfer_derived_value(source=kwargs['source'], dest=kwargs['dest'], interval=interval)
        else:
            raise NotImplementedError


class ScheduledJob:

    def __init__(self, job_id):
        self.job_id = job_id
        self.interval_minutes = Settings().interval_minutes(job_id)
        self.start_delay_minutes = Settings().start_delay_minutes(job_id)
        self.source = Settings().source(job_id)
        self.destination = Settings().destination(job_id)
