from celery import Celery
from celery.utils.log import get_task_logger

import requests
import datetime
import lxml.html
import re

from pool_list import db, cache
from pool_list.models import Pool, FifteenMinutePool

logger = get_task_logger(__name__)
celery = Celery('pool_list')


def grab_cloudflare(url, *args, **kwargs):
    sess = requests.Session()
    sess.headers = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:17.0) Gecko/20100101 Firefox/17.0"}
    safe_eval = lambda s: eval(s, {"__builtins__": {}}) if "#" not in s and "__" not in s else ""
    page = sess.get(url, *args, **kwargs)

    if "a = document.getElementById('jschl-answer');" in page.content:
        logger.info("Encountered CloudFlare anti-bot wall")
        # Cloudflare anti-bots is on
        html = lxml.html.fromstring(page.content)
        challenge = html.find(".//input[@name='jschl_vc']").attrib["value"]
        script = html.findall(".//script")[-1].text_content()
        domain_parts = url.split("/")
        domain = domain_parts[2]
        math = re.search(r"a\.value = (\d.+?);", script).group(1)

        answer = str(safe_eval(math) + len(domain))
        data = {"jschl_vc": challenge, "jschl_answer": answer}
        get_url = domain_parts[0] + '//' + domain + "/cdn-cgi/l/chk_jschl"
        return sess.get(get_url, params=data, headers={'referer': url}, *args, **kwargs)
    else:
        return page


@celery.task(bind=True)
def update_net_stats(self):
    """
    Updates things like network difficulty/hashrate, etc
    """
    try:
        # keep trying pools until we connect to one
        for pool in Pool.query.filter_by(typ='mpos'):
            try:
                r = grab_cloudflare(pool.api_link)
                data = r.json()
            except Exception:
                logger.warn("Unable to connect to {}".format(pool.api_link))
            else:
                try:
                    cache.set('netdiff', data['getpoolstatus']['data']['networkdiff'], 60 * 60)
                    cache.set('nethashrate', data['getpoolstatus']['data']['nethashrate'], 60 * 60)
                    cache.set('netheight', data['getpoolstatus']['data']['nextnetworkblock'], 60 * 60)
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
                r = grab_cloudflare(new_url)
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
        logger.error("Unhandled exception in update pools", exc_info=True)
        raise self.retry(exc=exc)


@celery.task(bind=True)
def update_pool(self, pool, slice_time):
    def log_pool(workers, hashrate, pool):
        logger.info("Receieved workers: {}; hashrate: {} for pool {}"
                    .format(workers, hashrate, pool.id))
        FifteenMinutePool.create(pool, 'workers', slice_time, workers)
        FifteenMinutePool.create(pool, 'hashrate', slice_time, hashrate)

    try:
        logger.info("Updating pool {}".format(pool.name))
        if pool.typ == 'mpos':
            try:
                r = grab_cloudflare(pool.api_link)
                data = r.json()
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                logger.warn("Unable to connect to pool {}".format(pool.api_link))
                return
            except Exception:
                logger.warn("Unkown problem scraping from pool {}"
                            .format(pool.api_link), exc_info=True)
                return

            try:
                workers = data['getpoolstatus']['data']['workers']
                hashrate = data['getpoolstatus']['data']['hashrate']
            except KeyError:
                logger.error("Values not given in proper MPOS format. "
                             "We got {}".format(data))
            else:
                log_pool(workers, hashrate, pool)

        elif pool.typ == 'p2pool':
            hashrate = 0
            workers = 0

            gaddr = pool.api_link.rsplit("/", 1)[0] + "/global_stats"
            try:
                r = grab_cloudflare(gaddr, timeout=2)
                data = r.json()
            except Exception:
                logger.warn("Unable to connect to p2pool node {}".format(gaddr))
            else:
                logger.info("Grabbed global stats {}".format(data))
                hashrate = data['pool_hash_rate']

            try:
                r = grab_cloudflare(pool.api_link)
                data = r.json()
            except Exception:
                logger.warn("Unable to connect to {}".format(pool.api_link))

            for addr in data.split(" "):
                addr = "http://" + addr.split(":")[0] + ":9171/local_stats"

                # to get an approx worker count we need to ping every node in
                # the list
                data = None
                try:
                    r = grab_cloudflare(addr, timeout=2)
                    data = r.json()
                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                    logger.warn("Unable to connect to p2pool node on 9171 {}".format(addr))
                except Exception:
                    logger.warn("Unkown problem connection to p2pool", exc_info=True)

                if data:
                    logger.debug("Grabbed stats {}".format(data))
                    workers += len(data['miner_hash_rates'])

            log_pool(workers, hashrate / 1000.0, pool)

        else:
            logger.warn("Unknown pool type: {}".format(pool.typ))

        db.session.commit()

    except Exception:
        logger.error("Unhandled exception in update_pool", exc_info=True)
