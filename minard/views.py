from minard import app
from flask import render_template, jsonify, request 
from minard.orca import session, CMOSRate
from minard.database import init_db, db_session
from minard.models import *
from threading import Thread, Event
import os
import shlex
from collections import deque
from subprocess import Popen, PIPE
from itertools import groupby
import atexit
from Queue import Queue, Empty
import sys

ON_POSIX = 'posix' in sys.builtin_module_names

home = os.environ['HOME']
tail = deque(maxlen=1000)

def enqueue_output(out, queue):
    for line in iter(out.readline, b''):
        queue.put(line)
    out.close()

def tail_worker(stop):
    p = Popen(shlex.split('ssh -i %s/.ssh/id_rsa_builder snotdaq@snoplusbuilder1 tail_log data_temp' % home), stdout=PIPE, bufsize=1, close_fds=ON_POSIX)
    q = Queue()
    t = Thread(target=enqueue_output, args=(p.stdout,q))
    t.daemon = True
    t.start()
    i = 0
    while not stop.is_set():
        try:
            line = q.get_nowait()#p.stdout.readline()
        except Empty:
            continue
        tail.append((i,line))
        i += 1
        if not line:
            break

    p.kill()
    p.wait()

stop = Event()
tail_thread = Thread(target=tail_worker,args=(stop,))
tail_thread.daemon = True
tail_thread.start() 

@atexit.register
def stop_worker():
    stop.set()
    tail_thread.join()

init_db()

PROJECT_NAME = 'Minard'
DEBUG = True
SECRET_KEY = "=S\t3w>zKIVy0n]b1h,<%|@EHBgfRJQ;A\rLC'[\x0blPF!` ai}/4W"

app.config.from_object(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/detector')
def hero():
    return render_template('detector.html')

@app.route('/daq/<name>')
def channels(name):
    if name == 'cmos':
        return render_template('channels.html',name=name, threshold=5000)
    elif name == 'base':
        return render_template('channels.html',name=name, threshold=80)

@app.route('/stream')
def stream():
    return render_template('stream.html')

@app.route('/alarms')
def alarms():
    return render_template('alarms.html')

@app.route('/builder')
def builder():
    return render_template('builder.html')

@app.route('/query')
def query():
    name = request.args.get('name','',type=str)

    if name == 'tail_log':
        id = request.args.get('id',0,type=int)
        return jsonify(value=[line for i, line in tail if i > id],id=max(zip(*tail)[0]))

    if name == 'sphere':
    	latest = PMT.latest()
	id, charge_occupancy = zip(*db_session.query(PMT.pmtid, PMT.chargeocc)\
            .filter(PMT.id == latest.id).all())
        return jsonify(id=id, values2=charge_occupancy)

    if name == 'l2_info':
        id = request.args.get('id',None,type=str)

        if id is not None:
            info = db_session.query(L2).filter(L2.id == id).one()
        else:
            info = db_session.query(L2).order_by(L2.id.desc()).first()

        return jsonify(value=dict(info))

    if name == 'nhit':
        latest = Nhit.latest()
        hist = [getattr(latest,'nhit%i' % i) for i in range(30)]
        bins = range(5,300,10)
        result = dict(zip(bins,hist))
        return jsonify(value=result)

    if name == 'pos':
        latest = Position.latest()
        hist = [getattr(latest,'pos%i' % i) for i in range(13)]
        bins = range(25,650,50)
        result = dict(zip(bins,hist))
        return jsonify(value=result)

    if name == 'events':
        value = db_session.query(L2.entry_time, L2.events).order_by(L2.entry_time.desc())[:600]
        t, y = zip(*value)
        result = {'t': [x.isoformat() for x in t], 'y': y}
        return jsonify(value=result)

    if name == 'events_passed':
        value = db_session.query(L2.entry_time, L2.passed_events).order_by(L2.entry_time.desc())[:600]
        t, y = zip(*value)
        result = {'t': [x.isoformat() for x in t], 'y': y}
        return jsonify(value=result)

    def total_seconds(td):
        """Returns the total number of seconds in the duration."""
        return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6

    if name == 'delta_t':
        value = db_session.query(L2).order_by(L2.entry_time.desc())[:600]
        result = {'t': [x.entry_time.isoformat() for x in value],
                  'y': [total_seconds(x.entry_time - x.get_clock()) for x in value]}
        return jsonify(value=result)

    if name == 'cmos':
        stats = request.args.get('stats','now',type=str)

        # if stats == 'avg':
        #     obj = cmos.avg
        # elif stats == 'max':
        #     obj = cmos.max
        # else:
        #     obj = cmos.now

        cmos_rates = session.query(CMOSRate).order_by(CMOSRate.timestamp.desc())

        cmos = {}
        for index, rates in groupby(cmos_rates, lambda x: x.index):
            if stats == 'now':
                cmos[index] = rates.next().value
            elif stats == 'avg':
                cmos[index] = sum(map(lambda x: x.value,rates))/len(rates)
            elif stats == 'max':
                cmos[index] = max(map(lambda x: x.value,rates))

        return jsonify(value=cmos)

    if name == 'base':
        stats = request.args.get('stats','',type=str)

        if stats == 'avg':
            obj = base.avg
        elif stats == 'max':
            obj = base.max
        else:
            obj = base.now

        return jsonify(value=obj)

    if name == 'alarms':
        alarms = db_session.query(Alarms)
        return jsonify(messages=[dict(x) for x in alarms])
