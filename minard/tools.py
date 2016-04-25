from __future__ import print_function
from datetime import datetime
import calendar
import json
import sys

def total_seconds(td):
    """Returns the total number of seconds contained in the duration."""
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6

def parseiso(timestr):
    """Convert an iso time string -> unix timestamp."""
    dt = datetime.strptime(timestr,'%Y-%m-%dT%H:%M:%S.%fZ')
    return calendar.timegm(dt.timetuple()) + dt.microsecond/1e6

def import_TELLIEDQ_ratdb(ratdbFile):
    runNumber = int(ratdbFile[-13:-9])
    json_data = open(ratdbFile).read()
    data = json.loads(json_data)
    print(data)
    #Get the runinformation from the tellie dq output
    runInformation = {}
    runInformation["expected_tellie_events"] = data["expected_tellie_events"]
    runInformation["actual_tellie_events"] = data["actual_tellie_events"]
    runInformation["average_nhit"] = data["average_nhit"]
    runInformation["greaterThanMaxNHitEvents"] = data["more_max_nhit_events"]
    runInformation ["fibre_firing"] = data["fibre_firing"]
    runInformation["fibre_firing_guess"] = data["fibre_firing_guess"]
    runInformation["peak_number"] = data["peak_number"]
    runInformation["prompt_peak_adc_count"] = data["prompt_peak_adc_count"]
    runInformation["pre_peak_adc_count"] = data["pre_peak_adc_count"]
    runInformation["late_peak_adc_count"] = data["late_peak_adc_count"]
    runInformation["run_length"] = data["run_length"]
    runInformation["pulse_delay_correct_proportion"]  = data["pulse_delay_efficiency"]

    return runNumber, data["checks"], runInformation


def import_SMELLIEDQ_ratdb(ratdbFile):
    runNumber = int(ratdbFile[-13:-9])
    json_data = open(ratdbFile).read()
    data = json.loads(json_data)
    subRunChecks = []
    subRunChecks.append(data["smellieFibreCheckSubrun"])
    subRunChecks.append(data["smellieNumberOfEventsSubrun"])
    subRunChecks.append(data["smelliePeakRatioSubrun"])
    subRunChecks.append(data["smellieFrequencyCheckSubrun"])
    subRunChecks.append( data["smellieNPeaksSubrun"])
    subRunChecks.append(data["smellieIntensityCheckSubrun"])
    return runNumber, data["checks"], subRunChecks 
