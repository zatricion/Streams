BROKER_URL = 'librabbitmq://'
CELERY_RESULT_BACKEND = 'librabbitmq://'

CELERY_TASK_SERIALIZER = 'msgpack'
CELERY_RESULT_SERIALIZER = 'msgpack'
CELERY_ACCEPT_CONTENT=['msgpack']
CELERY_ENABLE_UTC = True
