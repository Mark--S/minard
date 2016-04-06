#from sqlalchemy import engine, create_engine
import sqlalchemy
from minard import app

def get_latest_run(key_name='key'):
    """
    Returns the run number of the latest run to be added to the database.
    """
    user = app.config['DB_USER']
    password = app.config['DB_PASS']
    host = app.config['DB_HOST']
    database = app.config['DB_NAME']

    engine = sqlalchemy.create_engine('postgresql://%s:%s@%s/%s' % (user, password, host, database))

    conn = engine.connect()

    res = conn.execute("select run from run_state order by run desc limit 1")

    run = res.fetchone()[0]

    return run

def fetch_from_table_with_key(table_name,key,key_name='key'):
    user = app.config['DB_USER']
    password = app.config['DB_PASS']
    host = app.config['DB_HOST']
    database = app.config['DB_NAME']

    engine = sqlalchemy.create_engine('postgresql://%s:%s@%s/%s' % (user, password, host, database))

    try:
        conn = engine.connect()
    except Exception as e:
        #Do somethign here?
        raise e;
    command = "SELECT * FROM "+str(table_name)+" WHERE "+str(key_name)+" = "+str(key)
    res =  conn.execute(command)
    try:
        values = zip(res.keys(),res.fetchone())
    except TypeError:
        #Chances are this failed b/c the SELECT command didn't find anything
        raise ValueError(str(key_name)+" "+str(run)+" is not valid...probably")
    conn.close()
    return dict(values)

def get_detector_control_state(key):
    return fetch_from_table_with_key('detector_control',key)
    
def get_caen_state(key):
    return fetch_from_table_with_key('caen',key)

def get_mtc_state(key):
    return fetch_from_table_with_key('mtc',key)

def get_crate_state(key):
    return fetch_from_table_with_key('crate',key)

def get_fec_state(key):
    return fetch_from_table_with_key('fec',key)

def get_run_state(run):
    return fetch_from_table_with_key('run_state',run,key_name='run')
