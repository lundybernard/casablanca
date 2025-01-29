import logging


logging_config = dict(
    version=1,
    formatters={
        'f': {'format':
              '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'},
        'thread_formatter': {
            'format':
            '%(asctime)s %(threadName)-12s %(levelname)-8s %(message)s'
        }
    },
    handlers={
        'h': {
            'class': 'logging.StreamHandler',
            'formatter': 'f'
        },
        'thread_handler': {
            'class': 'logging.StreamHandler',
            'formatter': 'thread_formatter'
        }
    },
    loggers={
        'root': {
            'handlers': ['h'],
            'level': logging.DEBUG
        },
        'mod': {
            'handlers': ['h'],
            'level': logging.DEBUG
        },
        'thread': {
            'handlers': ['thread_handler'],
            'level': logging.DEBUG
        }
    }
)
