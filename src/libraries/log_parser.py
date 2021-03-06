import re
import time
import datetime
from libraries.utils import coroutine
from libraries.db import get_logdb

REGEX_SPECIAL_CHARS = r'([\.\*\+\?\|\(\)\{\}\[\]])'
REGEX_LOG_FORMAT_VARIABLE = r'\$([a-zA-Z0-9\_]+)'


def build_pattern(log_format):
    """
    Build regular expression to parse given format.
    :param log_format: format string to parse
    :return: regular expression to parse given format
    """
    pattern = re.sub(REGEX_SPECIAL_CHARS, r'\\\1', log_format)
    pattern = re.sub(REGEX_LOG_FORMAT_VARIABLE, '(?P<\\1>.*)', pattern)
    pattern = re.compile(pattern)
    # Initialize database with the field parsed from log format
    _ = get_logdb(pattern.groupindex.keys())
    return pattern


def process_log(log_file, pattern):
    f = open(log_file)
    db_processer = process_db()
    for l in f:
        matched = pattern.match(l)
        if matched:
            db_processer.send(matched.groupdict())

    db_processer.close()


@coroutine
def process_db():
    logdb = get_logdb()
    raws = []
    try:
        while True:
            raw = (yield)
            if raw is not None:
                raw['time_local'] = int(time.mktime(datetime.datetime.strptime(
                    raw['time_local'], "%d/%b/%Y:%H:%M:%S %z").timetuple()))
                if len(raws) < 1000:
                    raws.append(raw)
                else:
                    logdb.processmany(raws)
                    raws.clear()
                    raws.append(raw)

    except GeneratorExit:
        if raws:
            logdb.processmany(raws)
        pass
