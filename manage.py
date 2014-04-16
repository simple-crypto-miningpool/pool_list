import os
import logging

from flask.ext.script import Manager, Shell
from flask.ext.migrate import Migrate, MigrateCommand
from pool_list import create_app, db

app = create_app()
manager = Manager(app)
migrate = Migrate(app, db)

root = os.path.abspath(os.path.dirname(__file__) + '/../')

from pool_list.models import Pool
from pool_list.tasks import update_pools, update_payout_type
from flask import current_app, _request_ctx_stack

root = logging.getLogger()
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
root.addHandler(ch)
root.setLevel(logging.DEBUG)

hdlr = logging.FileHandler(app.config.get('manage_log_file', 'manage.log'))
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
root.addHandler(hdlr)
root.setLevel(logging.DEBUG)


@manager.option('name', help="The name of the pool to add to the list")
@manager.option('url', help="The url to navigate to the pool")
@manager.option('api_url', help="The url information used to gather data")
@manager.option('typ', help="The type of api")
def add_pool(typ, api_url, url, name):
    """ Manually create a BonusPayout for a user """
    Pool.create(name, typ, url, api_url)
    db.session.commit()


@manager.command
def init_db():
    """ Resets entire database to empty state """
    with app.app_context():
        db.session.commit()
        db.drop_all()
        db.create_all()


@manager.command
def update_pools_cmd():
    """ Manually runs the poll pools command """
    update_pools()


@manager.command
def update_payout_type_cmd():
    """ Manually runs the update payout types command for mpos pools"""
    update_payout_type()


def make_context():
    """ Setup a coinserver connection fot the shell context """
    app = _request_ctx_stack.top.app
    return dict(app=app)
manager.add_command("shell", Shell(make_context=make_context))
manager.add_command('db', MigrateCommand)


@manager.command
def runserver():
    current_app.run(debug=True, host='0.0.0.0')


if __name__ == "__main__":
    manager.run()
