from flask import render_template, Blueprint, current_app

from .models import Pool
from . import root, cache


main = Blueprint('main', __name__)


@cache.cached(timeout=10, key_prefix='last_block_time')
def top_pools():
    return sorted(Pool.query, key=lambda x: x.last_hashrate)[:20]


@main.route("/")
def home():
    pools = Pool.query.all()
    nethash = cache.get('nethashrate')
    nethash = '{:,} MH/s'.format(nethash) if nethash else "Unkn"
    netdiff = cache.get('netdiff')
    netdiff = '{:,}'.format(netdiff) if netdiff else "Unkn"
    netheight = cache.get('netheight')
    netheight = '{:,}'.format(netheight - 1) if netheight else "Unkn"
    total_workers = sum([p.last_workers for p in pools])

    return render_template('home.html',
                           total_workers=total_workers,
                           pools=pools,
                           nethash=nethash,
                           netdiff=netdiff,
                           netheight=netheight)
