from controller import Controller
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger


logging.basicConfig(
    filename='news2vid.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%d/%m/%Y %H:%M:%S')


def start_news2vid():
    while True:
        news2vid = Controller()
        news2vid.initialize_process()


if __name__ == "__main__":
    scheduler = BlockingScheduler()
    trigger = IntervalTrigger(hours=19)
    scheduler.add_job(start_news2vid, trigger, max_instances=3)
    try:
        scheduler.start()
    except BaseException as e:
        logging.debug(e)
