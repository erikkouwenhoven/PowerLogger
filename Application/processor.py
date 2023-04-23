import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from P1System.p1_interface import P1Interface
from SMASystem.sma_interface import SMAInterface
from DataHolder.data_holder import DataHolder
from WebServer.threaded_server import ThreadedServer
from Utils.settings import Settings


class Processor:
    """
        Initializes scheduled events, and receives and handles events.
    """

    c_PERSIST_JOB_ID = 'persist'

    def __init__(self, p1_interface: P1Interface, sma_interface: SMAInterface, data_holder: DataHolder):
        self.p1_interface = p1_interface
        self.sma_interface = sma_interface
        self.data_holder = data_holder
        self.webServer = ThreadedServer(self)
        self.scheduler = self.init_scheduler()

    def init_scheduler(self):
        scheduler = BackgroundScheduler()
        scheduler.add_job(self.do_persist, 'interval', minutes=Settings().persist_interval_minutes(),
                          start_date=datetime.now() + timedelta(minutes=Settings().persist_delay_minutes()), id=self.c_PERSIST_JOB_ID)
        scheduler.start()
        logging.debug("Scheduler started")
        return scheduler

    def p1SampleAcquired(self):
        p1_sample = self.p1_interface.getSample()
        logging.debug("p1SampleAcquired")
        solar_power = self.sma_interface.getCurrentPower()  # TODO acquire solar *before* p1 for better synchronicity?
        logging.debug(f"Solar power queried: {solar_power}")
        self.data_holder.addMeasurement(p1_sample, solar_power)

    def do_persist(self):
        logging.debug(f"do_persist")
        job = self.scheduler.get_job(job_id=self.c_PERSIST_JOB_ID)
        interval = job.trigger.interval
        logging.debug(f"do_persist, interval = {interval}")
        # Get the start time of the averaging interval
#                start_time = self.data_holder.get_most_recent_persistent_time()
        #   data = self.data_holder.get_average dit is een P1Sample
        #   data.filter
        #   self.db_interface.append(data)

    def getStr(self):
        return self.data_holder.real_time_data.str_last()

    def getRaw(self):
        return self.p1_interface.getRawLines()

    def getRealtimeDatadump(self):
        return self.data_holder.real_time_data.dump()

    def get_data(self):
        return self.data_holder.real_time_data.serialize()
