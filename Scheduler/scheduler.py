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
            if self.processor.check_job_parameters(sources=sched_job.sources,
                                                   dest=sched_job.destination,
                                                   operation=sched_job.operation,
                                                   operands=sched_job.operand) is True:
                kwargs = {'sources': sched_job.sources,
                          'dest': sched_job.destination,
                          'operation': sched_job.operation,
                          'operand': sched_job.operand,
                          'id': job_name,
                          }
                start_date = datetime.now() + timedelta(minutes=sched_job.delay_minutes if sched_job.delay_minutes else 0)
                scheduler.add_job(self.exec_job,
                                  'interval',
                                  minutes=sched_job.interval_minutes,
                                  kwargs=kwargs,
                                  start_date=start_date,
                                  id=job_name)
            else:
                logging.error(f"Job {sched_job} not started")
        scheduler.start()

    def exec_job(self, **kwargs):
        print(f"exec_job {kwargs['id']}")
        self.processor.process_derived_signal(sources=kwargs['sources'],
                                              dest=kwargs['dest'],
                                              operation=kwargs['operation'],
                                              operands=kwargs['operand'])


class ScheduledJob:

    def __init__(self, job_name: str):
        self.job_name = job_name
        self.sources = Settings().sched_job_sources(job_name)
        self.destination = Settings().sched_job_destination(job_name)
        self.interval_minutes = Settings().interval_minutes(job_name)
        self.delay_minutes = Settings().start_at_time(job_name)
        self.operation, self.operand = Settings().sched_job_operation(job_name)
