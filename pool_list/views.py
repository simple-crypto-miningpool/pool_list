from flask import render_template, Blueprint

from .models import Pool
from . import root, cache


main = Blueprint('main', __name__)


@cache.cached(timeout=10, key_prefix='last_block_time')
def top_pools():
    nethash = cache.get('nethashrate')
    sorted_pools = sorted(Pool.query, key=lambda x: x.last_hashrate)
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
    total_workers = sum([p.last_workers for p in pools])

    return render_template('home.html',
                           total_workers=total_workers,
                           pools=pools,
                           nethash=nethash,
                           netdiff=netdiff,
                           top_pools=top_pools(),
                           netheight=netheight)
    return render_template('home.html', pools=pools)

@main.route("/pool/<int:pool_id>")
def pool(pool_id):
    pool = Pool.query.filter_by(id=pool_id).first()
    return render_template('pool.html', pool=pool)
