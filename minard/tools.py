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
    return runNumber, data["checks"] 

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
