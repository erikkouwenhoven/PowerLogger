from datetime import datetime, timedelta
from enum import Enum, auto
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from Utils.magic_numbers import c_MINUTES_PER_HOUR
from Utils.time_delay import Period
from Utils.settings import Settings
from Application.Models.operation import Operation
from Application.processor import Processor
from Utils.time_delay import time_delay_minutes


class JobTrigger(Enum):
    PERIODIC = auto()
    CRON = auto()


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
            if self.check_job_parameters(sources=sched_job.sources,
                                         dest=sched_job.destination,
                                         operation=sched_job.operation,
                                         operands=sched_job.operand) is True:
                kwargs = {'sources': sched_job.sources,
                          'dest': sched_job.destination,
                          'operation': sched_job.operation,
                          'operand': sched_job.operand,
                          'id': job_name,
                          }
                if sched_job.trigger == JobTrigger.PERIODIC:
                    start_date = datetime.now() + timedelta(minutes=sched_job.delay_minutes if sched_job.delay_minutes else 0)
                    scheduler.add_job(self.exec_job,
                                      'interval',
                                      minutes=sched_job.interval_minutes,
                                      kwargs=kwargs,
                                      start_date=start_date,
                                      name=job_name,
                                      id=job_name)
                else:
                    crontabs = {  # minute, hour, day of month, month, day of week
                        Period.FIVEMIN: "*/5 * * * *",
                        Period.HOUR: f"{sched_job.delay_minutes} * * * *",
                        Period.DAY: f"{sched_job.delay_minutes} 0 * * *",
                        Period.MONTH: f"{sched_job.delay_minutes} 0 1 * *",
                        Period.YEAR: f"{sched_job.delay_minutes} 0 1 1 *",
                    }
                    assert sched_job.periodicity
                    scheduler.add_job(self.exec_job,
                                      # 'cron',
                                      CronTrigger.from_crontab(crontabs[sched_job.periodicity]),
                                      kwargs=kwargs,
                                      name=job_name,
                                      id=job_name)
            else:
                logging.error(f"Job {sched_job} not started")
        scheduler.start()
        self.scheduler.print_jobs(out=logging.StreamHandler().stream)

    def exec_job(self, **kwargs):
        self.processor.process_derived_signal(sources=kwargs['sources'],
                                              dest=kwargs['dest'],
                                              operation=kwargs['operation'],
                                              operands=kwargs['operand'])

    def check_job_parameters(self, sources: list[str], dest: str, operation: Operation, operands: list[str]) -> bool:
        for ds_str in sources + [dest]:
            if self.processor.data_holder.data_store(ds_str) is None:
                logging.error(f"check_job_parameters: Data store {ds_str} is unknown")
                return False

        source_signals: list[str] = []
        for source in sources:
            if data_store := self.processor.data_holder.data_store(source):
                source_signals += [signal for signal in data_store.signals]
        dest_signals = []
        if data_store := self.processor.data_holder.data_store(dest):
            dest_signals += [signal for signal in data_store.signals]
        if all([dest_signal in source_signals + Settings().derived_signals() for dest_signal in dest_signals]) is False and operation is not Operation.DIFF:
            logging.error(f"check_job_parameters: Not all destination signals ({dest_signals}) in source signals ({source_signals})")
            return False

        if operands == ["*"]:
            operands = dest_signals
        if all([operand in source_signals for operand in operands]) is False:
            logging.error(f"check_job_parameters: Not all operands ({operands}) in source signals ({source_signals})")
            return False

        if (len(dest_signals) == 1 or all([operand in source_signals for operand in operands])) is False:
            logging.error(f"check_job_parameters: The result signals of the operation are ambiguous: destination: {dest_signals}, operands: {operands}")
            return False

        if operation not in (Operation.AVG, Operation.INTEGRATE, Operation.VALUE) and len(operands) != 1:
            logging.error(f"check_job_parameters: The operation {operation} requires exactly one operand, instead {len(operands)} are found")
            return False

        operand_data_stores = list(filter(lambda ds: any(operand in ds.signals for operand in operands if ds),
                                          [self.processor.data_holder.data_store(src) for src in sources]))
        if len(operand_data_stores) != 1:
            logging.error(f"check_job_parameters: The operands {operands} should be all in the same data store")
            return False

        return True

    def __repr__(self):
        self.scheduler.print_jobs()


class ScheduledJob:
    """
    Houdt de gegevens van een scheduled job bij.
    Mogelijke trigger is: PERIODIC of CRON.
    Bij PERIODIC hoort interval_minutes en start_at_time; bij CRON hoort Periodicity en is start_at_time optioneel.
    De starttijd wordt gegeven (PERIODIC) of gezet op aanvang periode volgens periodicity in combinatie met eventuele
    start_at_time
    """

    def __init__(self, job_name: str):
        self.job_name = job_name
        self.sources = Settings().sched_job_sources(job_name)
        self.destination = Settings().sched_job_destination(job_name)
        self.interval_minutes = Settings().interval_minutes(job_name)
        self.periodicity = Settings().periodicity(job_name)
        self.delay_minutes = None
        start_at_time = Settings().start_at_time(job_name)
        if self.interval_minutes is None:  # cron
            assert self.periodicity is not None, f"Job {job_name}, val {self.periodicity}"
            if start_at_time is not None:
                hour_str = start_at_time.split(':')[0]
                hours = int(hour_str) if len(hour_str) > 0 else 0
                self.delay_minutes = hours * c_MINUTES_PER_HOUR + int(start_at_time.split(':')[1])
            else:
                self.delay_minutes = 0
        else:  # interval
            assert self.periodicity is None, f"Job {job_name}, val {self.periodicity}"
            if start_at_time is not None:
                self.delay_minutes = time_delay_minutes(start_at_time)
        self.operation, self.operand = Settings().sched_job_operation(job_name)

    @property
    def trigger(self) -> JobTrigger:
        if self.interval_minutes is None:
            return JobTrigger.CRON
        else:
            return JobTrigger.PERIODIC
