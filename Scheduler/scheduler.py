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
        job_names = Settings().scheduled_jobs()
        for job_name in job_names:
            sched_job = ScheduledJob(job_name)
            kwargs = {'sources': sched_job.sources,
                      'dest': sched_job.destination,
                      'operation': sched_job.operation,
                      'operand': sched_job.operand
                      }
            scheduler.add_job(self.exec_job,
                              'interval',
                              minutes=sched_job.interval_minutes,
                              kwargs=kwargs,
                              start_date=datetime.now() + timedelta(minutes=sched_job.start_delay_minutes),
                              job_id=job_name)
        scheduler.start()

    def exec_job(self, **kwargs):
        job_id = kwargs['id']
        job = self.scheduler.get_job(job_id=job_id)
        interval = job.trigger.interval
        self.processor.process_derived_signal(sources=kwargs['sources'],
                                              dest=kwargs['dest'],
                                              operation=kwargs['operation'],
                                              operand=kwargs['operand'])


class ScheduledJob:

    def __init__(self, job_name: str):
        self.job_name = job_name
        self.sources = Settings().sched_job_sources(job_name)
        self.destination = Settings().sched_job_destination(job_name)
        self.interval_minutes = Settings().interval_minutes(job_name)
        self.start_delay_minutes = Settings().start_delay_minutes(job_name)
        self.operation, self.operand = Settings().sched_job_operation(job_name)
