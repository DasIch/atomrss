"""
    tests.utils
    ~~~~~~~~~~~

    :copyright: 2016 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import structlog


def pass_through_proc(logger, method_name, event_dict):
    return event_dict


class RecordingLogger:
    def __init__(self):
        self.messages = []

    def msg(self, **kwargs):
        self.messages.append(kwargs)

    log = debug = info = warn = warning = msg
    failure = err = error = critical = exception = msg


def wrap_recording_logger(logger):
    return structlog.wrap_logger(logger, processors=[pass_through_proc])
