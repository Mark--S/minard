from __future__ import division
from __future__ import print_function
from minard import app
from flask import render_template, jsonify, request, redirect, url_for
from itertools import product
import time
from redis import Redis
from os.path import join
import json
from tools import total_seconds, parseiso, import_SMELLIEDQ_ratdb, import_TELLIEDQ_ratdb
import requests
from collections import deque, namedtuple
from timeseries import get_timeseries, get_interval, get_hash_timeseries
from timeseries import get_timeseries_field, get_hash_interval
from math import isnan
import os
import sys

import random

import pcadb
import ecadb

TRIGGER_NAMES = \
['100L',
 '100M',
 '100H',
 '20',
 '20LB',
 'ESUML',
 'ESUMH',
 'OWLN',
 'OWLEL',
 'OWLEH',
 'PULGT',
 'PRESCL',
 'PED',
 'PONG',
 'SYNC',
 'EXTA',
 'EXT2',
 'EXT3',
 'EXT4',
 'EXT5',
 'EXT6',
 'EXT7',
 'EXT8',
 'SRAW',
 'NCD',
 'SOFGT',
 'MISS']


class Program(object):
    def __init__(self, name, machine=None, link=None, description=None, expire=10):
        self.name = name
        self.machine = machine
        self.link = link
        self.description = description
        self.expire = expire

redis = Redis()

PROGRAMS = [Program('builder','builder1', description="event builder"),
            Program('L2-client','buffer1', description="L2 processor"),
            Program('L2-convert','buffer1',
                    description="zdab -> ROOT conversion"),
            Program('L1-delete','buffer1', description="delete L1 files"),
            Program('dflow_log',
		    description='copy log files from ORCA and builder'),
            Program('builder_copy', 'buffer1',
                    description="builder -> buffer transfer"),
            Program('buffer_copy', 'buffer1',
                    description="buffer -> grid transfer"),
            Program('builder_delete', 'buffer1',
                    description="builder deletion script"),
            Program('PCA','nlug', link='pcatellie',
		    description="monitor PCA data"),
            Program('ECA','nlug', link='eca', description="monitor ECA data"),
            Program('mtc','sbc', description="mtc server"),
            Program('data','daq1', description="data stream server"),
            Program('xl3','daq1', description="xl3 server"),
            Program('log','minard', description="log server")
]

@app.template_filter('timefmt')
def timefmt(timestamp):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(float(timestamp)))

@app.route('/status')
def status():
    return render_template('status.html', programs=PROGRAMS)

@app.route('/state')
@app.route('/state/<int:run>')
def state(run=None):
    import detector_state

    if run is None:
	run = detector_state.get_latest_run()

    try:
        run_state = detector_state.get_run_state(run)
    except Exception as err:
        return render_template('state.html',err = str(err))
        
    detector_control_state = None
    if run_state['detector_control'] is not None:
        detector_control_state = detector_state.get_detector_control_state(run_state['detector_control'])

    mtc_state = None
    if run_state['mtc'] is not None:
        mtc_state = detector_state.get_mtc_state(run_state['mtc'])

    caen_state = None
    if run_state['caen'] is not None:
        caen_state = detector_state.get_caen_state(run_state['caen'])

    crates_state =[None]*20
    for iCrate in range(20):
        if run_state['crate'+str(iCrate)] is not None:
            crates_state[iCrate] = detector_state.get_crate_state(run_state['crate'+str(iCrate)])

        
    return render_template('state.html',run=run,
					run_state = run_state,
                                        detector_control_state = detector_control_state,
                                        mtc_state = mtc_state,
                                        caen_state = caen_state,
                                        crates_state = crates_state,
                                        err = None)

@app.route('/l2')
def l2():
    step = request.args.get('step',3,type=int)
    height = request.args.get('height',20,type=int)
    if not request.args.get('step') or not request.args.get('height'):
        return redirect(url_for('l2',step=step,height=height,_external=True))
    return render_template('l2.html',step=step,height=height)

@app.route('/nearline')
@app.route('/nearline/<int:run>')
def nearline(run=None):
    if run is None:
	run = int(redis.get('nearline:current_run'))

    programs = redis.hgetall('nearline:%i' % run)

    return render_template('nearline.html', run=run, programs=programs)

@app.route('/get_l2')
def get_l2():
    name = request.args.get('name')

    try:
        files, times = zip(*redis.zrange('l2:%s' % name, 0, -1, withscores=True))
    except ValueError:
        # no files
        files = []
        times = []

    return jsonify(files=files,times=times)

@app.route('/graph')
def graph():
    name = request.args.get('name')
    start = request.args.get('start')
    stop = request.args.get('stop')
    step = request.args.get('step',1,type=int)
    return render_template('graph.html',name=name,start=start,stop=stop,step=step)

@app.route('/get_status')
def get_status():
    if 'name' not in request.args:
        return 'must specify name', 400

    name = request.args['name']

    up = redis.get('uptime:{name}'.format(name=name))

    if up is None:
        uptime = None
    else:
        uptime = int(time.time()) - int(up)

    return jsonify(status=redis.get('heartbeat:{name}'.format(name=name)),uptime=uptime)

@app.route('/view_log')
def view_log():
    name = request.args.get('name', '???')
    return render_template('view_log.html',name=name)

@app.route('/log', methods=['POST'])
def log():
    """Forward a POST request to the log server at port 8081."""
    import requests

    resp = requests.post('http://127.0.0.1:8081', headers=request.headers, data=request.form)
    return resp.content, resp.status_code, resp.headers.items()

@app.route('/tail')
def tail():
    name = request.args.get('name', None)

    if name is None:
        return 'must specify name', 400

    seek = request.args.get('seek', None, type=int)

    filename = join('/var/log/snoplus', name + '.log')

    try:
        f = open(filename)
    except IOError:
        return "couldn't find log file {filename}".format(filename=filename), 400

    if seek is None:
        # return last 100 lines
        lines = deque(f, maxlen=100)
    else:
        pos = f.tell()
        f.seek(0,2)
        end = f.tell()
        f.seek(pos)

        if seek > end:
            # log file rolled over
            try:
                prev_logfile = open(filename + '.1')
                prev_logfile.seek(seek)
                # add previous log file lines
                lines = prev_logfile.readlines()
            except IOError:
                return 'seek > log file length', 400

            # add new lines
            lines.extend(f.readlines())
        else:
            # seek to last position and readlines
            f.seek(seek)
            lines = f.readlines()

    lines = [line.decode('unicode_escape') for line in lines]

    return jsonify(seek=f.tell(), lines=lines)

@app.route('/')
def index():
    return redirect(url_for('snostream'))

@app.route('/docs/')
@app.route('/docs/<filename>')
@app.route('/docs/<dir>/<filename>')
@app.route('/docs/<dir>/<subdir>/<filename>')
def docs(dir='', subdir='', filename='index.html'):
    path = join('docs', dir, subdir, filename)
    return app.send_static_file(path)

@app.route('/snostream')
def snostream():
    if not request.args.get('step'):
        return redirect(url_for('snostream',step=1,height=20,_external=True))
    step = request.args.get('step',1,type=int)
    height = request.args.get('height',40,type=int)
    return render_template('snostream.html',step=step,height=height)

@app.route('/nhit')
def nhit():
  return render_template('nhit.html')

@app.route('/l2_filter')
def l2_filter():
    if not request.args.get('step'):
        return redirect(url_for('l2_filter',step=1,height=20,_external=True))
    step = request.args.get('step',1,type=int)
    height = request.args.get('height',40,type=int)
    return render_template('l2_filter.html',step=step,height=height)

@app.route('/detector')
def detector():
    return render_template('detector.html')

@app.route('/daq')
def daq():
    return render_template('daq.html')

@app.route('/alarms')
def alarms():
    return render_template('alarms.html')

CHANNELS = [crate << 9 | card << 5 | channel \
            for crate, card, channel in product(range(20),range(16),range(32))]

OWL_TUBES = [2032, 2033, 2034, 2035, 2036, 2037, 2038, 2039, 2040, 2041, 2042, 2043, 2044, 2045, 2046, 2047, 7152, 7153, 7154, 7155, 7156, 7157, 7158, 7159, 7160, 7161, 7162, 7163, 7164, 7165, 7166, 7167, 9712, 9713, 9714, 9715, 9716, 9717, 9718, 9719, 9720, 9721, 9722, 9723, 9724, 9725, 9726, 9727]

@app.route('/query')
def query():
    name = request.args.get('name','',type=str)

    if name == 'dispatcher':
        return jsonify(name=redis.get('dispatcher'))

    if name == 'nhit':
        seconds = request.args.get('seconds',type=int)

        now = int(time.time())

        p = redis.pipeline()
        for i in range(seconds):
            p.lrange('ts:1:{ts}:nhit'.format(ts=now-i),0,-1)
        nhit = map(int,sum(p.execute(),[]))
        return jsonify(value=nhit)

    if name in ('occupancy','cmos','base'):
        now = int(time.time())
        step = request.args.get('step',60,type=int)

        interval = get_hash_interval(step)

        i, remainder = divmod(now, interval)

        def div(a,b):
            if a is None or b is None:
                return None
            return float(a)/float(b)

        if remainder < interval//2:
            # haven't accumulated enough data for this window
            # so just return the last time block
            if redis.ttl('ts:%i:%i:%s:lock' % (interval,i-1,name)) > 0:
                # if ttl for lock exists, it means the values for the last
                # interval were already computed
                values = redis.hmget('ts:%i:%i:%s' % (interval, i-1, name),CHANNELS)
                return jsonify(values=values)
            else:
                i -= 1

        if name in ('cmos', 'base'):
            # grab latest sum of values and divide by the number
            # of values to get average over that window
            sum_ = redis.hmget('ts:%i:%i:%s:sum' % (interval,i,name),CHANNELS)
            len_ = redis.hmget('ts:%i:%i:%s:len' % (interval,i,name),CHANNELS)

            values = map(div,sum_,len_)
        else:
            hits = redis.hmget('ts:%i:%i:occupancy:hits' % (interval,i), CHANNELS)
            count = int(redis.get('ts:%i:%i:occupancy:count' % (interval,i)))
            if count > 0:
                values = [int(n)/count if n is not None else None for n in hits]
            else:
                values = [None]*len(CHANNELS)

        return jsonify(values=values)

@app.route('/get_alarm')
def get_alarm():
    try:
        count = int(redis.get('alarms:count'))
    except TypeError:
        return jsonify(alarms=[],latest=-1)

    if 'start' in request.args:
        start = request.args.get('start',type=int)

        if start < 0:
            start = max(0,count + start)
    else:
        start = max(count-100,0)

    alarms = []
    for i in range(start,count):
        value = redis.get('alarms:{0:d}'.format(i))

        if value:
            alarms.append(json.loads(value))

    return jsonify(alarms=alarms,latest=count-1)

@app.route('/owl_tubes')
def owl_tubes():
    """Returns the time series for the sum of all upward facing OWL tubes."""
    import numpy as np

    name = request.args['name']
    start = request.args.get('start', type=parseiso)
    stop = request.args.get('stop', type=parseiso)
    now_client = request.args.get('now', type=parseiso)
    step = request.args.get('step', type=int)
    method = request.args.get('method', 'avg')

    now = int(time.time())

    # adjust for clock skew
    dt = now_client - now
    start -= dt
    stop -= dt

    start = int(start)
    stop = int(stop)
    step = int(step)

    values = np.zeros((len(OWL_TUBES),len(range(start,stop,step))),float)
    for i, id in enumerate(OWL_TUBES):
        crate, card, channel = id >> 9, (id >> 5) & 0xf, id & 0x1f
        values[i] = get_hash_timeseries(name,start,stop,step,crate,card,channel,method)

    if method == 'max':
        values = np.nanmax(values,axis=0)
    else:
        values = np.nanmean(values,axis=0)

    return jsonify(values=[None if isnan(x) else x for x in values])

@app.route('/metric_hash')
def metric_hash():
    """Returns the time series for argument `names` as a JSON list."""
    name = request.args['name']
    start = request.args.get('start', type=parseiso)
    stop = request.args.get('stop', type=parseiso)
    now_client = request.args.get('now', type=parseiso)
    step = request.args.get('step', type=int)
    crate = request.args.get('crate', type=int)
    card = request.args.get('card', None, type=int)
    channel = request.args.get('channel', None, type=int)
    method = request.args.get('method', 'avg')

    now = int(time.time())

    # adjust for clock skew
    dt = now_client - now
    start -= dt
    stop -= dt

    start = int(start)
    stop = int(stop)
    step = int(step)

    values = get_hash_timeseries(name,start,stop,step,crate,card,channel,method)
    return jsonify(values=values)

@app.route('/metric')
def metric():
    """Returns the time series for argument `expr` as a JSON list."""
    args = request.args

    expr = args['expr']
    start = args.get('start',type=parseiso)
    stop = args.get('stop',type=parseiso)
    now_client = args.get('now',type=parseiso)
    step = args.get('step',type=int)

    now = int(time.time())

    # adjust for clock skew
    dt = now_client - now
    start -= dt
    stop -= dt

    start = int(start)
    stop = int(stop)
    step = int(step)

    if expr in ('L2:gtid', 'L2:run'):
        values = get_timeseries(expr, start, stop, step)
        return jsonify(values=values)

    if expr in ('gtid', 'run', 'subrun'):
        values = get_timeseries_field('trig', expr, start, stop, step)
        return jsonify(values=values)

    if expr in ('heartbeat','l2-heartbeat'):
        values = get_timeseries(expr,start,stop,step)
        return jsonify(values=values)

    if expr == u"0\u03bd\u03b2\u03b2":
        import random
        total = get_timeseries('TOTAL',start,stop,step)
        values = [int(random.random() < step/315360) if i else 0 for i in total]
        return jsonify(values=values)

    if '-' in expr:
        # e.g. PULGT-nhit, which means the average nhit for PULGT triggers
        # this is not a rate, so we divide by the # of PULGT triggers for
        # the interval instead of the interval length
        trig, value = expr.split('-')
        if(trig in TRIGGER_NAMES+['TOTAL']):
            if value=='Baseline':
                values = get_timeseries(expr,start,stop,step)
                counts = get_timeseries('baseline-count',start,stop,step)
            else:
                field = trig if trig=='TOTAL' else TRIGGER_NAMES.index(trig)
                values = get_timeseries_field('trig:%s' % value,field,start,stop,step)
                counts = get_timeseries_field('trig',field,start,stop,step)
            values = [float(a)/int(b) if a and b else None for a, b in zip(values,counts)]
        else:
            raise ValueError('unknown trigger type %s' % trig)
    else:
        if expr in TRIGGER_NAMES:
            field = TRIGGER_NAMES.index(expr)
            values = get_timeseries_field('trig',field,start,stop,step)
        elif expr == 'TOTAL':
            values = get_timeseries_field('trig','TOTAL',start,stop,step)
        else:
            values = get_timeseries(expr,start,stop,step)

        interval = get_interval(step)
        if expr in TRIGGER_NAMES or expr in ('TOTAL','L1','L2','ORPHANS','BURSTS'):
            # trigger counts are zero by default
            values = map(lambda x: int(x)/interval if x else 0, values)
        else:
            values = map(lambda x: int(x)/interval if x else None, values)

    return jsonify(values=values)

@app.route('/eca')
def eca():

    runs = ecadb.runs_after_run(0)      
    return render_template('eca.html', runs=runs)
 
@app.route('/eca_run_detail/<run_number>')
def eca_run_detail(run_number):
    run_type = redis.hget('eca-run-%i' % int(run_number),'run_type')
    return render_template('eca_run_detail_%s.html' % run_type, run_number=run_number)      

@app.route('/eca_status_detail/<run_number>')
def eca_status_detail(run_number):
    run_type = redis.hget('eca-run-%i' % int(run_number),'run_type')

    def statusfmt(status_int):
        if status_int == 1:
            return 'Flag Raised'
        if status_int == 0:
            return 'Pass'

    def testBit(word, offset):
        int_type = int(word)
        offset = int(offset)
        mask = 1 << offset
        result = int_type & mask
        if result == 0:
            return 0
        if result == pow(2,offset):
            return 1

    run_status = int(ecadb.get_run_status(run_number))

    return render_template('eca_status_detail_%s.html' % run_type,
			    run_number=run_number,statusfmt=statusfmt,testBit=testBit,run_status=run_status)      

@app.route('/pcatellie', methods=['GET'])
def pcatellie():
    
    def boolfmt(bool_string):
        bool_value = bool_string == '1'
        return "Pass" if not bool_value else "Fail"
    
    def boolclass(bool_string):
        bool_value = bool_string == '1'
        return "success" if not bool_value else "danger"
    
    start_run = request.args.get("start_run", 0)
    installed_only = request.args.get("installed_only", False)    
    runs = pcadb.runs_after_run(start_run)
    # Deal with expired runs
    runs = [run for run in runs if (len(run) > 0)]      
    fibers = list()
    for fiber in pcadb.FIBER_POSITION:
        runs_for_fiber = [run for run in runs 
                          if int(run["fiber_number"]) == fiber[0]]
        sorted_runs = sorted(runs_for_fiber, 
                             key=lambda run: (run["pca_status"] == "True", int(run["run_number"])),
                             reverse=True)
        pca_run = sorted_runs[0]["run_number"] if sorted_runs else ""  
        pca_result = sorted_runs[0]["pca_status"] if sorted_runs else ""                   
        fibers.append({'fiber_number': fiber[0],
                       'node': fiber[1], 
                       'ab': fiber[2], 
                       'is_installed': fiber[3], 
                       'is_dead': fiber[4],
                       'fiber_type': fiber[5],
                       'pca_run': pca_run,
                       'pca_result': pca_result})
            
    # ['Fiber', 'Node', 'AB', 'IsInstalled', 'IsDead', 'Type'],
       
    return render_template('pcatellie.html',
                           runs=runs,
                           boolfmt=boolfmt,
                           boolclass=boolclass,
                           fibers=fibers,
                           start_run=start_run,
                           installed_only=installed_only,
    )    
    
@app.route('/pca_run_detail/<run_number>')
def pca_run_detail(run_number):
    
    return render_template('pca_run_detail.html',
                            run_number=run_number)      
@app.route('/calibdq')
def calibdq():
        return render_template('calibdq.html')
   
@app.route('/calibdq_tellie')
def calibdq_tellie():
    run_numbers = []
    run_info = []
    root_dir = "/home/mark/Documents/PHD/DQTests/TELLIEDQTest/"
    ratOutputs = os.listdir(root_dir)
    for files in ratOutputs:
        if "DATAQUALITY_RECORDS" in files and ".ratdb" in files and "p2" in files and ".sw" not in files:
            print(files)
            run_num, check_params, runInformation =  import_TELLIEDQ_ratdb(os.path.join(root_dir,files))
            if "dqtellieproc" in check_params:
                run_numbers.append(run_num)
                run_info.append(check_params["dqtellieproc"])
    print(run_numbers)
    print(run_info)
    return render_template('calibdq_tellie.html',run_numbers=run_numbers,run_info=run_info)

@app.route('/calibdq_tellie/<run_number>/')
def calibdq_tellie_run_number(run_number):
    run_num = 0
    plots = []
    runInformation = {}
    subRunChecks = 0
    root_dir = os.path.join(app.static_folder,"images/TELLIEDQPlots_"+str(run_number))
    root_tellie_dir = "/home/mark/Documents/PHD/DQTests/TELLIEDQTest/"
    ratOutputs = os.listdir(root_tellie_dir)
    for files in ratOutputs:
        if "DATAQUALITY_RECORDS" in files and ".ratdb" in files and "p2" and run_number in files and ".sw" not in files:
            print(files)
            run_num, check_params, runInformation =  import_TELLIEDQ_ratdb(os.path.join(root_tellie_dir,files))
    
    images = os.listdir(root_dir)
    print(images)
    #Array to store the titles of the plots
    titleArray = ["Hit Map","Calibrated Hit Time Plot","TAC Plot"]
    for image in images:
        img_url = url_for("static",filename=os.path.join("images/TELLIEDQPlots_"+str(run_number),image))
        plots.append(img_url)
    return render_template('calibdq_tellie_run.html',run_number=run_number,plots=plots, titles=titleArray, runInformation=runInformation)




@app.route('/calibdq_smellie')
def calibdq_smellie():
    run_numbers = []
    run_info = []
    root_dir = os.path.join(os.environ["MINARD_DQ_RATDB_DIR"],"SMELLIE")
    ratOutputs = os.listdir(root_dir)
    for files in ratOutputs:
        if "DATAQUALITY_RECORDS" in files and ".ratdb" in files and ".sw" not in files:
           print(files)
           run_num, check_params, subRunCheck, runInformation =  import_SMELLIEDQ_ratdb(os.path.join(root_dir,files))
           if "DQSmellieProc" in check_params:
               run_numbers.append(run_num)
               run_info.append(check_params["DQSmellieProc"])
               print(run_numbers)
    return render_template('calibdq_smellie.html',run_numbers=run_numbers,run_info=run_info)

@app.route('/calibdq_smellie/<run_number>')
def calibdq_smellie_run_number(run_number):
    run_num = 0
    run_info = []
    subRunChecks = 0
    root_dir = os.path.join(os.environ["MINARD_DQ_RATDB_DIR"],"SMELLIE")
    ratOutputs = os.listdir(root_dir)
    for files in ratOutputs:
        if "DATAQUALITY_RECORDS" in files and ".ratdb" in files and ".sw" not in files:
           run_num, check_params, subRunCheck, runInformation =  import_SMELLIEDQ_ratdb(os.path.join(root_dir,files))
           if run_num == int(run_number):
               if "DQSmellieProc" in check_params:
                   subRunChecks = subRunCheck
    
    return render_template('calibdq_smellie_run.html',run_number=run_number,subRunChecks=subRunChecks)


@app.route('/calibdq_smellie/<run_number>/<subrun_number>')
def calibdq_smellie_subrun_number(run_number,subrun_number):
    rinInfo = {}
    root_dir = os.path.join(os.environ["MINARD_DQ_RATDB_DIR"],"SMELLIE")
    ratOutputs = os.listdir(root_dir)
    for files in ratOutputs:
        if "DATAQUALITY_RECORDS" in files and ".ratdb" in files and ".sw" not in files:
           run_num, check_params, subRunCheck, runInformation =  import_SMELLIEDQ_ratdb(os.path.join(root_dir,files))
           if run_num == int(run_number):
               if "DQSmellieProc" in check_params:
                   runInfo = runInformation
    run_num = 0
    plots = []
    subRunChecks = 0
    root_dir = os.path.join(app.static_folder,"images/DQ/SMELLIEDQPlots_"+str(run_number),"subrun_"+str(subrun_number))
    images = os.listdir(root_dir)
    #Sort the entire array by check number
    images.sort(key= lambda x : int(x[x.find("Check")+5]))
    #Sort the images for check 1
    images[:4] = sorted(images[:4])
    #Swap two elements to make the trigger cut plots together
    images[1], images[2]  =  images[2], images[1]
    #Sort the images for check 3
    images[5:6] = sorted(images[5:6])
    #Sort the images for check 3
    images[7:] = sorted(images[7:])
    #Array to store the titles of the plots
    titleArray = ["Hit Maps for all Events","Hit Maps for events passing the trigger cut","Hit Maps for events failing the trigger cut","NHits Plots for all trigger types","NHits vs Trigger Type","NHits vs time between events","Time between events passing the trigger cut","First Peak Hit Map","Second Peak Hit Map","100th Point on CAEN trace distribution"]
    for image in images:
        img_url = url_for("static",filename=os.path.join("images/DQ/SMELLIEDQPlots_"+str(run_number)+"/subrun_"+str(subrun_number),image))
        print(img_url)
        plots.append(img_url)
    return render_template('calibdq_smellie_subrun.html',run_number=run_number,subrun_number=subrun_number,plots=plots, titles=titleArray, runInformation = runInfo) 
