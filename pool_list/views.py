import calendar
import time
import datetime
import yaml

from flask import (current_app, request, render_template, Blueprint, abort,
                   jsonify, g, session, Response)
from lever import get_joined

from .models import Pool
from . import db, root, cache


main = Blueprint('main', __name__)


@main.route("/")
def home():
    return render_template('home.html')
