from celery import Celery
from celery.utils.log import get_task_logger

import requests

from pool_list import db, cache
from pool_list.models import Pool

logger = get_task_logger(__name__)
celery = Celery('pool_list')


@celery.task(bind=True)
def update_pools(self):
    """
    Loop through the pools table and accumulate new stats for each pool
    """
    try:
        pass
    except Exception as exc:
        logger.error("Unhandled exception in estimating pplns", exc_info=True)
        raise self.retry(exc=exc)
