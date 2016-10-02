from datetime import timedelta

CELERY_BROKER_URL = 'redis://localhost'
CELERY_RESULT_BACKEND = 'redis://localhost'
CELERYBEAT_SCHEDULE = {
    'query-demolition-permits': {
    'task': 'tasks.query_demolition_permits',
    'schedule': timedelta(hours=1),
	},
}

DEPLOYMENT = "production"