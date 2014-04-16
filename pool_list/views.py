from flask import render_template, Blueprint, current_app

from .models import Pool
from . import root, cache


main = Blueprint('main', __name__)


@main.route("/")
def home():
    pools = Pool.query.all()
    return render_template('home.html', pools=pools)
