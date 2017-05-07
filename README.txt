This is a testcase for the retry logic in requests/urllib3 that for me exhibits
deadlocks under gevent.

I've also included a version using system threads which exhibits the same
behavior, but doesn't raise an exception.

To run this:

$ virtualenv foo
$ source foo/bin/activate
$ pip install -r requests-retry-pool-hang/requirements.txt
$ time requests-retry-pool-hang/retry_pool_hang_gevent.py --retry http://google.com/404

Running with or without ssl/proxies all seem to produce the same result -- that
supplying --retry causes a deadlock after a time:

(foo) mattb@mattb-mbp2:~/src/requests-retry-pool-hang HEAD$ time ./retry_pool_hang.py --retry http://google.com/404
Traceback (most recent call last):
  File "./retry_pool_hang.py", line 56, in <module>
    main()
  File "./retry_pool_hang.py", line 53, in main
    gevent.joinall(workers)
  File "/Users/mattb/src/foo/lib/python2.7/site-packages/gevent/greenlet.py", line 649, in joinall
    return wait(greenlets, timeout=timeout, count=count)
  File "/Users/mattb/src/foo/lib/python2.7/site-packages/gevent/hub.py", line 1038, in wait
    return list(iwait(objects, timeout, count))
  File "/Users/mattb/src/foo/lib/python2.7/site-packages/gevent/hub.py", line 985, in iwait
    item = waiter.get()
  File "/Users/mattb/src/foo/lib/python2.7/site-packages/gevent/hub.py", line 939, in get
    Waiter.get(self)
  File "/Users/mattb/src/foo/lib/python2.7/site-packages/gevent/hub.py", line 899, in get
    return self.hub.switch()
  File "/Users/mattb/src/foo/lib/python2.7/site-packages/gevent/hub.py", line 630, in switch
    return RawGreenlet.switch(self)
gevent.hub.LoopExit: ('This operation would block forever', <Hub at 0x1098f7c30 select default pending=0 ref=0 resolver=<gevent.resolver_thread.Resolver at 0x109bc4bd0 pool=<ThreadPool at 0x10948a9d0 0/10/10>> threadpool=<ThreadPool at 0x10948a9d0 0/10/10>>)

real    0m39.536s
user    0m0.488s
sys     0m0.168s

I've repro'd this under OSX:

(foo) mattb@mattb-mbp2:~/src/requests-retry-pool-hang HEAD$ sw_vers
ProductName:    Mac OS X
ProductVersion: 10.11.6
BuildVersion:   15G1421
(tve)mattb@mattb-mbp2:~ $ python --version
Python 2.7.10

and Ubuntu 16.04:

(foo) mattb@matt:~/requests-retry-pool-hang HEAD$ cat /etc/issue
Ubuntu 16.04.2 LTS \n \l
(foo) mattb@matt:~/requests-retry-pool-hang HEAD$ python --version
Python 2.7.12

With python lib versions:

(foo) mattb@matt:~/requests-retry-pool-hang HEAD$ pip freeze
appdirs==1.4.3
gevent==1.2.1
greenlet==0.4.12
packaging==16.8
pyparsing==2.2.0
requests==2.13.0
six==1.10.0


It's also interesting to look at connections opened while this is running:

(foo)mattb@mattb-mbp2:~ $ while true; do sudo lsof -P -p $(ps aux | grep retry | grep python2 | awk '{print $2}') |  grep TCP | awk '{print $NF}' | sort | uniq -c; sleep 2; done
     10 (ESTABLISHED)
     10 (ESTABLISHED)
     10 (ESTABLISHED)
     10 (ESTABLISHED)

Essentially one per greenlet without retry, and 2-3 per greenlet with retries.
