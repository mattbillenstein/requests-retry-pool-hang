#!/usr/bin/env python2

import gevent.monkey
gevent.monkey.patch_all()

import gevent
import sys
import requests
from requests.packages.urllib3.util import Retry

proxies = None
if '--proxies' in sys.argv:
    proxies = {'http': 'http://127.0.0.1:3128', 'https': 'http://127.0.0.1:3128'}

url = 'http://google.com/404'
if '--ssl' in sys.argv:
    url = 'https://google.com/404'

def make_session():
    session = requests.Session()

    retry = 10
    if '--retry' in sys.argv:
        retry = Retry(
            total = 3,
            backoff_factor = 1.0,
            raise_on_status = False,
            status_forcelist = [404],
        )

    request_adapter = requests.adapters.HTTPAdapter(
        pool_maxsize = 200,
        pool_connections = 200,
        pool_block = True,
        max_retries = retry,
    )
    session.mount('http://', request_adapter)
    session.mount('https://', request_adapter)
    return session

session = make_session()

def worker():
    while 1:
        res = session.get(url, proxies=proxies)
        assert res.status_code == 404

def main():
    workers = []
    for i in xrange(10):
        g = gevent.spawn(worker)
        workers.append(g)
    gevent.joinall(workers)

if __name__ == '__main__':
    main()
