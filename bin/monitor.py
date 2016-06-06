#!/usr/bin/env python
from __future__ import print_function
import sys
import urllib
import urllib2
from base64 import b64encode
import threading
import logging
import socket
from itertools import starmap, repeat
from functools import wraps
import time

NOTIFY = {'notify': True}

def retry(ExceptionToCheck, tries=4, delay=3, backoff=2, logger=None):
    """Retry calling the decorated function using an exponential backoff.

    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry

    :param ExceptionToCheck: the exception to check. may be a tuple of
        exceptions to check
    :type ExceptionToCheck: Exception or tuple
    :param tries: number of times to try (not retry) before giving up
    :type tries: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param backoff: backoff multiplier e.g. value of 2 will double the delay
        each retry
    :type backoff: int
    :param logger: logger to use. If None, print
    :type logger: logging.Logger instance
    """
    def deco_retry(f):

        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck, e:
                    msg = "%s, Retrying in %d seconds..." % (str(e), mdelay)
                    if logger:
                        logger.warning(msg)
                    else:
                        print(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry

def repeatfunc(func, times=None, *args):
    """Repeat calls to func with specified arguments.

    Example:  repeatfunc(random.random)
    """
    if times is None:
        return starmap(func, repeat(args))
    return starmap(func, repeat(args, times))

@retry((urllib2.URLError,socket.timeout), tries=10, delay=1, backoff=1)
def post(url, data, auth=None, retries=10):
    """
    Sends a POST request containing `data` to url. `auth` should be a
    tuple containing (username, password).
    """
    if not url.startswith('http://'):
        url = 'http://' + url

    request = urllib2.Request(url)
    if auth:
        request.add_header('Authorization', 'Basic %s' % b64encode('%s:%s' % auth))

    params = urllib.urlencode(data)
    response = urllib2.urlopen(request, params)
    return response.read()

class HTTPHandler(logging.Handler):
    """
    Sends log messages to the monitoring server using POST requests.
    If the log record has an attribute 'notify', then the log message
    will trigger an alert on the monitoring site.

    Example:
        logger.addHandler(HTTPHandler(name,host))
        logger.info("Hello, world!")
        logger.info("Hello, world!", extra=NOTIFY)
    """
    def __init__(self, name, host, auth=None):
        logging.Handler.__init__(self)
        self.name = name
        self.host = host
        self.auth = auth

    def emit(self, record):
        data = {'name': self.name, 'level': record.levelno, 'message': record.msg}
        if hasattr(record,'notify') and record.notify:
            data['notify'] = True
        response = post('{host}/monitoring/log'.format(host=self.host), data, self.auth)
        if response.strip() != 'ok':
            raise RuntimeError('POST got response {response}'.format(response=response))

def post_heartbeat(host, name, auth=None):
    """
    Sends a POST request every second to the monitoring server
    indicating that the process is still running.
    """
    data = {'name': name, 'status': 'ok'}
    try:
        response = post('{host}/monitoring/heartbeat'.format(host=host), data, auth)
    except urllib2.URLError:
        print("Failed to send heartbeat.", file=sys.stderr)
    else:
        if response.strip() != 'ok':
            print('POST got response {response}'.format(response=response), file=sys.stderr)

    timer = threading.Timer(1.0, post_heartbeat, args=(host, name, auth))
    # set the thread as a daemon to exit the program cleanly
    # when the main thread finishes
    timer.daemon = True
    timer.start()

def set_up_root_logger(host, name, auth=None):
    """Sets up the root logger to send log messages to the monitoring server."""
    root_logger = logging.getLogger()
    root_logger.addHandler(HTTPHandler(name, host, auth))
    root_logger.setLevel(logging.DEBUG)

if __name__ == '__main__':
    import optparse
    import traceback
    import re

    parser = optparse.OptionParser()
    parser.add_option('--local', action='store_true', dest='local',
                      help='post heartbeat/logs to localhost')
    options, args = parser.parse_args()

    if len(args) < 1:
        sys.exit("must specify name")

    name = args[0]

    if options.local:
        host = 'localhost:50000'
        auth = None
    else:
        host = 'minard.sp.snolab.ca'
        auth = None

    post_heartbeat(host, name, auth)
    set_up_root_logger(host, name, auth)

    p = re.compile('(ERROR|WARNING|INFO|SUCCESS|DEBUG)\s*-\s*(.*)')

    for line in repeatfunc(sys.stdin.readline):
        if not line:
            break

        match = p.match(line)

        if match is None:
            try:
                logging.info(line.strip())
            except urllib2.URLError, e:
                print(e, file=sys.stderr)
        else:
            level, message = match.groups()

            try:
                if level == 'ERROR':
                    logging.error(message)
                elif level == 'WARNING':
                    logging.warning(message)
                elif level == 'SUCCESS':
                    logging.log(21, message, extra=NOTIFY)
                elif level == 'INFO':
                    logging.info(message)
                elif level == 'DEBUG':
                    logging.debug(message)
                else:
                    logging.info(line)
            except urllib2.URLError, e:
                print(e, file=sys.stderr)
