from flask import current_app

from pool_list import create_app
from pool_list.tasks import celery
from celery.bin.worker import main


app = create_app(celery=True)

with app.app_context():
    # import celerybeat settings
    celery.config_from_object('celeryconfig')
    celery.conf.update(current_app.config['celery'])
    current_app.logger.info("Celery worker powering up... BBBVVVRRR!")
    main(app=celery)
