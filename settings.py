BROKER_URL = 'amqp://guest:guest@localhost'
CELERY_RESULT_BACKEND = 'amqp://guest:guest@localhost'
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
config = {"folder_out": "/", "bitrates_size_dict": {240:200, 480:600, 720:800}}
