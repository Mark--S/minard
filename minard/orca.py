from __future__ import division
from websno.stream import OrcaJSONStream
from threading import Timer, Lock
import time
from collections import defaultdict

expire = 60

cmos = lambda: None # just a mock object
cmos.lock = Lock()
cmos.items = []

def update(obj):
    with obj.lock:
        now = time.time()
        obj.items = filter(lambda x: x[2] > now - expire, obj.items)

    group = defaultdict(list)

    for k, v, t in obj.items:
        group[k].append(v)

    obj.max = {k: max(v) for k, v in group.iteritems()}
    obj.avg = {k: sum(v)/len(v) for k, v in group.iteritems()}
    obj.now = {k: v[-1] for k, v in group.iteritems()}

    Timer(5,update,args=(obj,)).start()

def callback(output):
    for item in output:
        if 'key' in item and item['key'] == 'cmos_rate':
            crate, card = item['crate_num'], item['slot_num']
            rate = item['v']['rate']

            with cmos.lock:
                for i in range(len(rate)):
                    j = (crate << 16) | (card << 8) | i
                    cmos.items.append((j,rate[i],time.time()))

orca_stream = OrcaJSONStream('tcp://localhost:5028',callback)
orca_stream.start()

print 'update(cmos)'
update(cmos)