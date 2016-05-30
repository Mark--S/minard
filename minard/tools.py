from __future__ import print_function
from datetime import datetime
import calendar
import json
import simplejson
import sys
import re

def total_seconds(td):
    """Returns the total number of seconds contained in the duration."""
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6

def parseiso(timestr):
    """Convert an iso time string -> unix timestamp."""
    dt = datetime.strptime(timestr,'%Y-%m-%dT%H:%M:%S.%fZ')
    return calendar.timegm(dt.timetuple()) + dt.microsecond/1e6

def import_TELLIEDQ_ratdb(ratdbFile):
    runNumber = int(re.search('DATAQUALITY_RECORDS_(.*)_p', ratdbFile).group(1))
    print("RUN NUMBER: "+str(runNumber))
    print(ratdbFile)
    json_data = open(ratdbFile).read()
    data = json.loads(json_data)
    #Get the runinformation from the tellie dq output
    runInformation = {}
    runInformation["expected_tellie_events"] = data["expected_tellie_events"]
    runInformation["actual_tellie_events"] = data["actual_tellie_events"]
    runInformation["average_nhit"] = data["average_nhit"]
    runInformation["greaterThanMaxNHitEvents"] = data["more_max_nhit_events"]
    runInformation ["fibre_firing"] = data["fibre_firing"]
    runInformation["fibre_firing_guess"] = data["fibre_firing_guess"]
    runInformation["peak_number"] = data["peak_numbers"]
    runInformation["prompt_peak_adc_count"] = data["prompt_peak_adc_count"]
    runInformation["pre_peak_adc_count"] = data["pre_peak_adc_count"]
    runInformation["late_peak_adc_count"] = data["late_peak_adc_count"]
    runInformation["subrun_run_times"] = data["subrun_run_times"]
    runInformation["pulse_delay_correct_proportion"]  = data["pulse_delay_efficiency"]

    #Run Information for the subruns
    runInformation["subrun_numbers"] = data["subrun_numbers"]
    runInformation["avg_nhit_check_subruns"] = data["avg_nhit_check"]
    runInformation["max_nhit_check_subruns"] = data["max_nhit_check"]
    runInformation["peak_number_check_subruns"] = data["peak_number_check"]
    runInformation["prompt_peak_amplitude_check_subruns"] = data["prompt_peak_amplitude_check"]
    runInformation["prompt_peak_adc_count_check_subruns"] = data["prompt_peak_adc_count_check"]
    runInformation["adc_peak_time_spacing_check_subruns"] = data["adc_peak_time_spacing_check"]
    runInformation["pulse_delay_efficiency_check_subruns"] = data["pulse_delay_efficiency_check"]
    runInformation["subrun_run_length_check"] = data["subrun_run_length_check"]
    runInformation["correct_fibre_check_subruns"] = data["correct_fibre_check"]
    runInformation["trigger_check_subruns"] = data["trigger_check"]
    print(runInformation)

    return runNumber, data["checks"], runInformation


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
