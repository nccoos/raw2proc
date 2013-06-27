#!/usr/bin/env python
# Last modified:  Time-stamp: <2009-04-01 08:47:51 haines>
"""
parse datestr from cr1000 files to create monthly files

input file
/seacoos/data/nccoos/level0/crow/crow_csi_loggernet_yyyymmdd-yyyymmdd.dat

Output form
/seacoos/data/nccoos/level0/crow/yyyy_mm/wq/csi_wq_yyyy_mm.dat
/seacoos/data/nccoos/level0/crow/yyyy_mm/flow/csi_flow_yyyy_mm.dat

load data file
parse lines for time YYYY, jjj, HHMM
what year and month?

create YYYY_MM directory and output file if does not exist.
write line to YYYY_MM/csi_loggernet_yyyy_mm.dat output file

"""

REAL_RE_STR = '\\s*(-?\\d(\\.\\d+|)[Ee][+\\-]\\d\\d?|-?(\\d+\\.\\d*|\\d*\\.\\d+)|-?\\d+)\\s*'

import sys
import os
import re
from procutil import *

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
    
    import numpy
    from datetime import datetime
    from time import strptime
    import math

    p = os.path.split(fn)
    (loggertype, id, datatype) = p[1].split('_')

    #  set this_month to now
    this_month_str = this_month()

    # skip first 4 lines but write these four lines to top of monthly files
    print lines[0:4]
    for line in lines[4:]:
        # split line 
        sw = re.split(',', line)

        if len(sw)>=1:
            # print line
            # get sample datetime from sw[0]
            sample_dt = scanf_datetime(sw[0], fmt='"%Y-%m-%d %H:%M:%S"')
            month_str = '%4d_%02d' % sample_dt.timetuple()[0:2]
        else:
            # not a well-formed line, so skip to next line
            print 'ill-formed time, line not to be copied: ' + line
            continue

        if datatype=='Data15Min.dat':
            data_dir = os.path.join(p[0],'flow',month_str)
            ofn_prefix = '%s_%s' % (id.lower(), 'flow')
        elif datatype=='DataHourly.dat':
            data_dir = os.path.join(p[0],'wq',month_str)
            ofn_prefix = '%s_%s' % (id.lower(), 'wq')
            
        if not os.path.isdir(data_dir):
            print 'Creating directory: '+data_dir
            os.mkdir(data_dir)
            
        ofn = os.path.join(data_dir, ofn_prefix)
        ofn = '_'.join([ofn, month_str])
        ofn = '.'.join([ofn, 'dat'])

        # delete previous existing month file so start fresh
        if os.path.exists(ofn) and (month_str != this_month_str):
            print 'Deleting file: '+ofn
            os.remove(ofn)
            
        if os.path.exists(ofn):
            f = open(ofn, 'a')
            f.write(line)
            f.close
        else:
            print 'Creating file: '+ofn
            f = open(ofn, 'w')
            # write first four header lines to each new month
            for l in lines[0:4]:
                f.write(l)
            f.write(line)
            f.close()

        this_month_str = month_str
        
    # for line
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

from raw2proc import *

def test1(fn):
    lines = load_data(fn)
    return parse_csi_loggernet(fn, lines)

def spin():
    fns = [
        '/seacoos/data/nccoos/level0/crow/CR1000_CBC_Data15Min.dat',
        '/seacoos/data/nccoos/level0/crow/CR1000_CBC_DataHourly.dat',
        '/seacoos/data/nccoos/level0/meet/CR1000_MOW_Data15Min.dat',
        '/seacoos/data/nccoos/level0/meet/CR1000_MOW_DataHourly.dat',
        ]

    for fn in fns:
        test1(fn)


if __name__ == '__main__':
    pass
    # fn = '/seacoos/data/nccoos/level0/crow/cbc_loggernet_20050325-20070726.dat'

    # 
    # fn = sys.argv[1]
    # try:
    #     test1(fn)
    # except:
    #     pass
    
