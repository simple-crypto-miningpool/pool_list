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


@manager.command
def init_db():
    """ Resets entire database to empty state """
    with app.app_context():
        db.session.commit()
        db.drop_all()
        db.create_all()


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
