#!/usr/bin/env python
# Last modified:  Time-stamp: <2009-04-01 12:15:11 haines>
"""
parse datestr from cr1000 files to create monthly files
intended to run on Loggernet Computer

input file
C:/Campbellsci/Loggernet/CR1000_CBC_15MinData.dat
C:/Campbellsci/Loggernet/CR1000_CBC_HourlyData.dat

Output form
C:/Campbellsci/Loggernet//cbc/wq/cbc_wq_yyyy_mm.dat
C:/Campbellsci/Loggernet//cbc/flow/cbc_flow_yyyy_mm.dat

load data file
parse lines for time YYYY-MM-DD HH:MM:SS
what year and month?

create monthly output file for the present month of data
this will delete any old and rewrite a new one from the original
Loggernet Data file

There doesn't seem to be a clear cut way to do this in Loggernet
with LNBackup or LNSplit.  

"""

REAL_RE_STR = '\\s*(-?\\d(\\.\\d+|)[Ee][+\\-]\\d\\d?|-?(\\d+\\.\\d*|\\d*\\.\\d+)|-?\\d+)\\s*'

import sys
import os
import re

import procutil

def parse_csi_loggernet(fn, lines):
    """

    From FSL (CSI datalogger program files):
    Example data:
    
    TOA5,CR1000_CBC,CR1000,5498,CR1000.Std.11,CPU:UNC_CrowBranch.CR1,1554,Data15Min
    TIMESTAMP,RECORD,RainIn_Tot,WaterLevelFt,Flow
    TS,RN,,,
    ,,Tot,Smp,Smp
    2009-01-22 15:30:00,0,0,0,0
    2009-01-22 15:45:00,1,0,0,0
    2009-01-22 16:00:00,2,0.01,0,0
    2009-01-22 16:15:00,3,0,0,0

    TOA5,CR1000_CBC,CR1000,5498,CR1000.Std.11,CPU:UNC_CrowBranch.CR1,1554,DataHourly
    TIMESTAMP,RECORD,SondeTempC,SpCond,DOSat,DOmg,pH,Turb,BattVolt_Min
    TS,RN,,,,,,,
    ,,Smp,Smp,Smp,Smp,Smp,Smp,Min
    2009-01-22 16:00:00,0,2.68,0.533,7.63,-46.8,-1.4,0,11.99
    2009-01-22 17:00:00,1,3.07,0.553,7.62,-46.6,-1.4,0,11.96
    2009-01-22 18:00:00,2,3.45,0.548,7.62,-46.5,-1.4,0,11.91
    2009-01-22 19:00:00,3,3.53,0.546,7.62,-46.3,-1.4,0,11.89
    2009-01-22 20:00:00,4,3.59,0.547,7.62,-46.3,-1.4,0,11.86
    2009-01-22 21:00:00,5,3.55,0.545,7.61,-46.2,-0.7,0,11.84
    2009-01-22 22:00:00,6,3.47,0.545,7.62,-46.3,4.2,0,11.81
    2009-01-22 23:00:00,7,3.37,0.545,7.62,-46.4,-0.7,0,11.8
    2009-01-23 00:00:00,8,3.28,0.545,7.62,-46.5,4.2,0,11.78
    2009-01-23 01:00:00,9,3.17,0.546,7.62,-46.7,-0.9,0,11.76
    2009-01-23 02:00:00,10,3,0.549,7.63,-46.8,-1.3,0,11.74
    2009-01-23 03:00:00,11,2.95,0.55,7.64,-47.3,-1.4,0,11.73
    2009-01-23 04:00:00,12,2.89,0.552,7.63,-47.2,-1.4,0,11.71
    2009-01-23 05:00:00,13,2.8,0.554,7.64,-47.3,-1.4,0,11.69
    2009-01-23 06:00:00,14,2.72,0.554,7.64,-47.6,-1.3,0,11.68
        
    """
    
    p = os.path.split(fn)
    (loggertype, id, datatype) = p[1].split('_')

    this_month_str = procutil.this_month()

    if datatype=='Data15Min.dat':
        data_dir = os.path.join(p[0],id.lower(),'flow')
        ofn_prefix = '%s_%s' % (id.lower(), 'flow')
        samples_per_hour = 4
    elif datatype=='DataHourly.dat':
        data_dir = os.path.join(p[0],id.lower(),'wq')
        ofn_prefix = '%s_%s' % (id.lower(), 'wq')
        samples_per_hour = 1

    if not os.path.isdir(data_dir):
        print ' ... Creating directory: '+data_dir
        os.mkdir(data_dir)
            
    ofn = os.path.join(data_dir, ofn_prefix)
    ofn = '_'.join([ofn, this_month_str])
    ofn = '.'.join([ofn, 'dat'])

    # delete previous existing month file so start fresh
    if os.path.exists(ofn):
        print ' ... ... Deleting file: '+ofn
        os.remove(ofn)

    # only read last part of each loggernet data file
    starti = -32*samples_per_hour*24
    endi = -1   
    # unless there is less than one month of data in the file
    if len(lines)<32*samples_per_hour*24+4:
        starti = 4

    # skip first 4 lines but write these four lines to top of monthly files
    for line in lines[starti:endi]:
        # split line 
        sw = re.split(',', line)

        if len(sw)>=1:
            # print line
            # get sample datetime from sw[0]
            sample_dt = procutil.scanf_datetime(sw[0], fmt='"%Y-%m-%d %H:%M:%S"')
            file_month_str = '%4d_%02d' % sample_dt.timetuple()[0:2]
        else:
            # not a well-formed line, so skip to next line
            print 'ill-formed time, line not to be copied: ' + line
            continue

        if file_month_str == this_month_str:
            if os.path.exists(ofn):
                f = open(ofn, 'a')
                f.write(line)
                f.close
            else:
                print ' ... ... Creating file: '+ofn
                print lines[0:4]
                # write first four header lines to each new month
                # and the first line of data for the month
                f = open(ofn, 'w')
                for l in lines[0:4]:
                    f.write(l)
                f.write(line)
                f.close()
        
    # for each line
    return 
    
def load_data(inFile):
    lines=None
    if os.path.exists(inFile):
        f = open(inFile, 'r')
        lines = f.readlines()
        f.close()
        if len(lines)<=0:
            print 'Empty file: '+ inFile           
    else:
        print 'File does not exist: '+ inFile
    return lines

def spin():
    #fns = [
    #    './test_data/CR1000_CBC_Data15Min.dat',
    #    './test_data/CR1000_CBC_DataHourly.dat',
    #    './test_data/CR1000_MOW_Data15Min.dat',
    #    './test_data/CR1000_MOW_DataHourly.dat',
    #    ]
    fns = [
        'C:/Campbellsci/Loggernet/CR1000_CBC_Data15Min.dat',
        'C:/Campbellsci/Loggernet/CR1000_CBC_DataHourly.dat',
        'C:/Campbellsci/Loggernet/CR1000_MOW_Data15Min.dat',
        'C:/Campbellsci/Loggernet/CR1000_MOW_DataHourly.dat',
        ]

    for fn in fns:
        lines = load_data(fn)
        parse_csi_loggernet(fn, lines)
    
    return


if __name__ == '__main__':
    try:
        spin()
    except:
        pass
    
