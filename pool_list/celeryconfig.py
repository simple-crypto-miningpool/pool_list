from datetime import timedelta
from flask import current_app


caching_tasks = {
}

database_tasks = {
    'update_pools': {
        'task': 'pool_list.tasks.update_pools',
        'schedule': timedelta(minutes=15),
    },
    'update_net_state': {
        'task': 'pool_list.tasks.update_net_stats',
        'schedule': timedelta(minutes=15),
    },
}

CELERYBEAT_SCHEDULE = caching_tasks
# we want to let celery run in staging mode where it only handles updating
# caches while the prod celery runner is handling real work. Allows separate
# cache databases between stage and prod
if not current_app.config.get('stage', False):
    CELERYBEAT_SCHEDULE.update(database_tasks)
