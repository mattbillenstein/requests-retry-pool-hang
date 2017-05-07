#!/usr/bin/env python2

import sys
import threading
import time
import requests
from requests.packages.urllib3.util import Retry

url = sys.argv[-1]
assert url.startswith('http'), url

def make_session():
    session = requests.Session()

    retry = 10
    if '--retry' in sys.argv:
        retry = Retry(
            total = 3,
            backoff_factor = 0.1,
            raise_on_status = False,
            status_forcelist = [404],
        )

    request_adapter = requests.adapters.HTTPAdapter(
        pool_maxsize = 50,
        pool_connections = 10,
        pool_block = True,
        max_retries = retry,
    )
    session.mount('http://', request_adapter)
    session.mount('https://', request_adapter)
    return session

session = make_session()

def worker():
    while 1:
        res = session.get(url)
        assert res.status_code == 404
        sys.stdout.write('.')
        sys.stdout.flush()

def main():
    workers = []
    for i in xrange(10):
        t = threading.Thread(target=worker)
        t.daemon = True
        workers.append(t)
        t.start()

    while 1:
        time.sleep(3)
        if all(not _.isAlive() for _ in workers):
            break

if __name__ == '__main__':
    main()
