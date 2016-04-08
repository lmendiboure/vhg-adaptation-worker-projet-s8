BROKER_URL = 'amqp://guest:guest@localhost'
CELERY_RESULT_BACKEND = 'amqp://guest:guest@localhost'
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
