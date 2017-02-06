from __future__ import print_function
from datetime import datetime
import calendar
import json
import simplejson
import sys
import re
import couchdb
import os

def total_seconds(td):
    """Returns the total number of seconds contained in the duration."""
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6

def parseiso(timestr):
    """Convert an iso time string -> unix timestamp."""
    dt = datetime.strptime(timestr,'%Y-%m-%dT%H:%M:%S.%fZ')
    return calendar.timegm(dt.timetuple()) + dt.microsecond/1e6

def import_HLDQ_runnumbers():
    server = couchdb.Server("http://snoplus:"+os.environ["COUCHDB_PASSWORD"]+"@couch.snopl.us")
    dqDB = server["data-quality"]
    runNumbers = []
    for row in tellieDB.view('_design/data-quality/_view/runs'):
        runNum = int(row)
        if runNum not in runNumbers:
            runNumbers.append(runNum)
    return runNumbers


def import_SMELLIE_runnumbers():
    server = couchdb.Server("http://snoplus:"+os.environ["COUCHDB_PASSWORD"]+"@couch.snopl.us")
    smellieDB = server["smellie"]
    runNumbers = []
    for row in tellieDB.view('_design/runNumbers/_view/runNumbers'):
        runNum = int(row.key)
        if runNum not in runNumbers:
            runNumbers.append(runNum)
    return runNum 

def import_SMELLIEDQ_ratdb(ratdbFile):
    runNumber = int(re.search('DATAQUALITY_RECORDS_(.*)_p', ratdbFile).group(1))
    print("RUN NUMBER: "+str(runNumber))
    json_data = open(ratdbFile).read()
    print("FILE:  "+str(ratdbFile))
    json_data = json_data.replace("inf","-9999999")
    json_data = json_data.replace("-nan","-9999999")
    json_data = json_data.replace("nan","-9999999")
    print(json_data)
    data = simplejson.loads(json_data)
    runInformation =  {}
    subRunChecks = []
    subRunChecks.append(data["smellieFibreCheckSubrun"])
    subRunChecks.append(data["smellieNumberOfEventsSubrun"])
    subRunChecks.append(data["smellieFrequencyCheckSubrun"])
    subRunChecks.append(data["smellieIntensityCheckSubrun"])
    runInformation["events_failing_nhit_failing_trigger"] = data["events_failing_nhit_failing_trigger"] 
    runInformation["events_failing_nhit_passing_trigger"] = data["events_failing_nhit_passing_trigger"]
    runInformation["events_passing_nhit_and_trigger"] = data["events_passing_nhit_and_trigger"]
    runInformation["events_passing_nhit_failing_trigger"] = data["events_passing_nhit_failing_trigger"]
    runInformation["fibre_calculated_subrun"] = data["fibre_calculated_subrun"]
    runInformation["fibre_expected_subrun"] = data["fibre_expected_subrun"]
    runInformation["frequency_actual_subrun"] = data["frequency_actual_subrun"]
    runInformation["frequency_expected_subrun"] = data["frequency_expected_subrun"]
    runInformation["mean_nhit_smellie_trigger_subrun"] = data["mean_nhit_smellie_trigger_subrun"]
    runInformation["nhit_event_next_to_trigger_event"] = data["nhit_event_next_to_trigger_event"]
    runInformation["nhit_event_no_adjacent_trigger"] = data["nhit_event_no_adjacent_trigger"]
    runInformation["number_events_expected_subrun"] = data["number_events_expected_subrun"]
    runInformation["trigger_event_no_adjacent_nhit"] = data["trigger_event_no_adjacent_nhit"]
    print(data)
    runInformation["laser_type"] = data["laser_type"]
    runInformation["laser_wavelengths"] = data["laser_wavelengths"]
    runInformation["laser_intensities"] = data["laser_intensities"]
    runInformation["fixed_laser_intensities_and_superK_wavelengths"] = data["fixed_intensities_and_superk_wavelengths"]
    
    return runNumber, data["checks"], subRunChecks , runInformation

def import_TELLIE_runnumbers():
    server = couchdb.Server("http://snoplus:"+os.environ["COUCHDB_PASSWORD"]+"@couch.snopl.us")
    tellieDB = server["telliedb"]
    runNumbers = []
    for row in tellieDB.view('_design/ratdb/_view/select_time'):
        if row.key[0] != "TELLIE_RUN":
            continue
        runNum = int(row.key[1])
        if runNum not in runNumbers:
            runNumbers.append(runNum)
    return runNumbers

def import_TELLIEDQ_ratdb(runNumber):
    server = couchdb.Server("http://snoplus:"+os.environ["COUCHDB_PASSWORD"]+"@couch.snopl.us")
    dqDB = server["data-quality"]
    data = None
    for row in dqDB.view('_design/data-quality/_view/runs'):
        if(int(row.key) == runNumber):
            runDocId = row['id']
            try:
                data = dqDB.get(runDocId)["checks"]["dqtellieproc"]
            except KeyError:
                print("Got key error: %d" % runNumber)
                return runNumber, -1, -1 
    if data==None:
        return runNumber, -1, -1 
    
    checkDict = {}
    checkDict["fibre"] = data["fibre"]
    checkDict["pulse_delay"] = data["pulse_delay"]
    checkDict["avg_nhit"] = data["avg_nhit"]
    checkDict["peak_amplitude"] = data["peak_amplitude"]
    checkDict["max_nhit"] = data["max_nhit"]
    checkDict["trigger"] = data["trigger"]
    checkDict["run_length"] = data["run_length"]
    checkDict["peak_number"] = data["peak_number"]
    checkDict["prompt_time"] = data["prompt_time"]
    checkDict["peak_time"] = data["peak_time"]

    #Get the runinformation from the tellie dq output
    runInformation = {}
    runInformation["expected_tellie_events"] = data["check_params"]["expected_tellie_events"]
    runInformation["actual_tellie_events"] = data["check_params"]["actual_tellie_events"]
    runInformation["average_nhit"] = data["check_params"]["average_nhit"]
    runInformation["greaterThanMaxNHitEvents"] = data["check_params"]["more_max_nhit_events"]
    runInformation ["fibre_firing"] = data["check_params"]["fibre_firing"]
    runInformation["fibre_firing_guess"] = data["check_params"]["fibre_firing_guess"]
    runInformation["peak_number"] = data["check_params"]["peak_numbers"]
    runInformation["prompt_peak_adc_count"] = data["check_params"]["prompt_peak_adc_count"]
    runInformation["pre_peak_adc_count"] = data["check_params"]["pre_peak_adc_count"]
    runInformation["late_peak_adc_count"] = data["check_params"]["late_peak_adc_count"]
    runInformation["subrun_run_times"] = data["check_params"]["subrun_run_times"]
    runInformation["pulse_delay_correct_proportion"]  = data["check_params"]["pulse_delay_efficiency"]

    #Run Information for the subruns
    runInformation["subrun_numbers"] = data["check_params"]["subrun_numbers"]
    runInformation["avg_nhit_check_subruns"] = data["check_params"]["avg_nhit_check"]
    runInformation["max_nhit_check_subruns"] = data["check_params"]["max_nhit_check"]
    runInformation["peak_number_check_subruns"] = data["check_params"]["peak_number_check"]
    runInformation["prompt_peak_amplitude_check_subruns"] = data["check_params"]["prompt_peak_amplitude_check"]
    runInformation["prompt_peak_adc_count_check_subruns"] = data["check_params"]["prompt_peak_adc_count_check"]
    runInformation["adc_peak_time_spacing_check_subruns"] = data["check_params"]["adc_peak_time_spacing_check"]
    runInformation["pulse_delay_efficiency_check_subruns"] = data["check_params"]["pulse_delay_efficiency_check"]
    runInformation["subrun_run_length_check"] = data["check_params"]["subrun_run_length_check"]
    runInformation["correct_fibre_check_subruns"] = data["check_params"]["correct_fibre_check"]
    runInformation["trigger_check_subruns"] = data["check_params"]["trigger_check"]

    return runNumber, checkDict, runInformation



def roundToInt(number):
    print("NUMBER IS")
    print(number)
    return int(round(number))

