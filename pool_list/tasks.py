from celery import Celery
from celery.utils.log import get_task_logger

import requests
import datetime

from pool_list import db, cache
from pool_list.models import Pool, FifteenMinutePool

logger = get_task_logger(__name__)
celery = Celery('pool_list')


@celery.task(bind=True)
def update_net_stats(self):
    """
    Updates things like network difficulty/hashrate, etc
    """
    try:
        # keep trying pools until we connect to one
        for pool in Pool.query.filter_by(typ='mpos'):
            try:
                r = requests.get(pool.api_link)
                data = r.json()
            except Exception:
                logger.warn("Unable to connect to {}".format(pool.api_link))
                logger.debug(r.text)
            else:
                try:
                    cache.set('netdiff', data['getpoolstatus']['data']['networkdiff'])
                    cache.set('nethashrate', data['getpoolstatus']['data']['nethashrate'])
                    cache.set('netheight', data['getpoolstatus']['data']['nextnetworkblock'])
                except KeyError:
                    logger.warn("Values not given in proper MPOS format. "
                                "We got {}".format(data))
                else:
                    break

        db.session.commit()
    except Exception as exc:
        logger.error("Unhandled exception in estimating pplns", exc_info=True)
        raise self.retry(exc=exc)


@celery.task(bind=True)
def update_payout_type(self):
    """
    Attempts to update the payout type of MPOS pools
    """
    try:
        for pool in Pool.query.filter_by(typ='mpos'):
            # replace the action in the url string...
            new_url = pool.api_link.replace('getpoolstatus', 'getpoolinfo')

            try:
                r = requests.get(new_url)
                data = r.json()
            except Exception:
                logger.warn("Unable to connect to {}".format(pool.api_link))
                logger.debug(r.text)
            else:
                try:
                    pool.payout_type = data['getpoolinfo']['data']['payout_system'].capitalize()
                except KeyError:
                    logger.error("Values not given in proper MPOS format. "
                                 "We got {}".format(data))
                    logger.debug(data)

        db.session.commit()

    except Exception as exc:
        logger.error("Unhandled exception in estimating pplns", exc_info=True)
        raise self.retry(exc=exc)


@celery.task(bind=True)
def update_pools(self):
    """
    Loop through the pools table and accumulate new stats for each pool
    """
    # ensure the time falls within the 15 minute window
    slice_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)

    try:
        for pool in Pool.query:
            # distribute the update tasks among celery workers
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
