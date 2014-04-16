from celery import Celery
from celery.utils.log import get_task_logger

import requests
import datetime

from pool_list import db, cache
from pool_list.models import Pool, FifteenMinutePool

logger = get_task_logger(__name__)
celery = Celery('pool_list')


@celery.task(bind=True)
def update_pools(self):
    """
    Loop through the pools table and accumulate new stats for each pool
    """
    # ensure the time falls within the 15 minute window
    slice_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)

    try:
        for pool in Pool.query:
            update_pool.delay(pool, slice_time)

    except Exception as exc:
        logger.error("Unhandled exception in estimating pplns", exc_info=True)
        raise self.retry(exc=exc)


@celery.task(bind=True)
def update_pool(self, pool, slice_time):
    def log_pool(workers, hashrate, pool):
        logger.info("Receieved workers: {}; hashrate: {} for pool {}"
                    .format(workers, hashrate, pool.id))
        FifteenMinutePool.create(pool, 'workers', slice_time, workers)
        FifteenMinutePool.create(pool, 'hashrate', slice_time, hashrate)

    try:
        if pool.typ == 'mpos':
            try:
                r = requests.get(pool.api_link)
                data = r.json()
            except Exception:
                logger.warn("Unable to connect to {}".format(pool.api_link))

            try:
                workers = data['getpoolstatus']['data']['workers']
                hashrate = data['getpoolstatus']['data']['hashrate']
            except KeyError:
                logger.error("Values not given in proper MPOS format. "
                             "We got {}".format(data))

            log_pool(workers, hashrate, pool)

    except Exception:
        logger.error("Unhandled exception in estimating pplns", exc_info=True)
