from flask import render_template, Blueprint, current_app

import time
import datetime
import calendar

from .models import Pool, FifteenMinutePool
from . import root, cache, db


main = Blueprint('main', __name__)


@cache.cached(timeout=10, key_prefix='last_block_time')
def top_pools():
    nethash = cache.get('nethashrate')
    sorted_pools = sorted([p for p in Pool.query if p.last_hashrate], key=lambda x: x.last_hashrate)
    top_total = sum([p.last_hashrate for p in sorted_pools[:20]])
    other_total = sum([p.last_hashrate for p in sorted_pools[19:]])
    top = [dict(label=pool.name, value=pool.last_hashrate)
           for pool in sorted_pools[:20]]
    if nethash:
        nethash = nethash / 1000000.0
        unknown_total = nethash - top_total - other_total
        top.append(dict(label="Unlisted Sources", value=unknown_total))
    if other_total > 0:
        top.append(dict(label="Other Pools", value=other_total))
    return top


@main.route("/")
def home():
    pools = Pool.query.all()
    nethash = cache.get('nethashrate')
    nethash = '{:,} MH/s'.format(round(nethash / 1000000.0, 2)) if nethash else "Unkn"
    netdiff = cache.get('netdiff')
    netdiff = '{:,}'.format(round(netdiff, 2)) if netdiff else "Unkn"
    netheight = cache.get('netheight')
    netheight = '{:,}'.format(netheight - 1) if netheight else "Unkn"
    total_workers = sum([p.last_workers or 0 for p in pools])

    return render_template('home.html',
                           total_workers=total_workers,
                           pools=pools,
                           nethash=nethash,
                           netdiff=netdiff,
                           top_pools=top_pools(),
                           netheight=netheight)
    return render_template('home.html', pools=pools)


def get_typ(typ, typ_string, pool_id, filter_func=lambda x: x):
    """ Gets the latest slices of a specific size. window open toggles
    whether we limit the query to the window size or not. We disable the
    window when compressing smaller time slices because if the crontab
    doesn't run we don't want a gap in the graph. This is caused by a
    portion of data that should already be compressed not yet being
    compressed. """
    # grab the correctly sized slices
    base = db.session.query(typ).filter_by(typ=typ_string, pool=pool_id)
    grab = typ.floor_time(datetime.datetime.utcnow()) - typ.window

    step = int(typ.slice_seconds)
    end = ((int(time.time()) // step) * step) - step
    start = end - int(typ.window.total_seconds()) + step

    vals = {calendar.timegm(slc.time.utctimetuple()): slc.value
            for slc in base.filter(typ.time >= grab)}

    lst = []
    for stamp in xrange(start, end, step):
        if stamp in vals:
            lst.append((stamp * 1000, filter_func(vals[stamp])))
        else:
            lst.append((stamp * 1000, 0))

    return lst


@cache.memoize(timeout=360)
def pool_stats(pool):
    hashrate_data = get_typ(FifteenMinutePool, pool_id=pool.id,
                            typ_string='hashrate', filter_func=lambda x: x / 1000.0)
    worker_data = get_typ(FifteenMinutePool, pool_id=pool.id,
                          typ_string='workers')
    return hashrate_data, worker_data


@main.route("/pool/<int:pool_id>")
def pool(pool_id):
    pool = Pool.query.filter_by(id=pool_id).first()
    hashrate_data, worker_data = pool_stats(pool)
    return render_template('pool.html',
                           pool=pool,
                           hashrate_data=hashrate_data,
                           worker_data=worker_data)
