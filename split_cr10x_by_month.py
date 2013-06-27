#!/usr/bin/env python
# Last modified:  Time-stamp: <2009-10-08 16:49:23 haines>
"""
parse yr, yrday, time from csi loggernet and create monthly files

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

def parse_csi_loggernet(fn, lines):
    """

    From FSL (CSI datalogger program files):
    
    15 Output_Table  15.00 Min
    1 15 L
    2 Year_RTM  L
    3 Day_RTM  L
    4 Hour_Minute_RTM  L
    5 Rain15sec_TOT  L
    6 SonLevlft  L
    7 SonFlow  L
    8 PrDepthft  L
    9 PrFlowcfs  L
    
    1 Output_Table  60.00 Min
    1 1 L
    2 Year_RTM  L
    3 Day_RTM  L
    4 Hour_Minute_RTM  L
    5 H2OTempC  L
    6 SpCond  L
    7 DOSat  L
    8 DOmg  L
    9 PH  L
    10 Turb  L
    11 BattVolts  L

    Example data:
    
    1,2005,83,1600,16.47,0,.4,.04,8.14,115.5,14.25
    15,2005,83,1615,0,4.551,-.547,.897,.885
    15,2005,83,1630,0,4.541,.727,.908,1.005
    15,2005,83,1645,0,4.537,6.731,.878,.676
    15,2005,83,1700,0,4.537,6.731,.83,.167
    1,2005,83,1700,16.57,0,.4,.03,8.03,145.7,13.08
    15,2005,83,1715,0,4.547,5.29,.847,.347
    15,2005,83,1730,0,4.541,.908,.842,.287
    15,2005,83,1745,0,4.547,7.3,.853,.407
    15,2005,83,1800,0,4.551,6.939,.855,.437
    1,2005,83,1800,15.65,0,.2,.02,7.91,111.3,12.98

    """

    import numpy
    from datetime import datetime
    from time import strptime
    import math

    p = os.path.split(fn)
    id = p[1].split('_')[0]
    
    for line in lines:
        csi = []
        # split line and parse float and integers
        sw = re.split(',', line)
        for s in sw:
            m = re.search(REAL_RE_STR, s)
            if m:
                csi.append(float(m.groups()[0]))

        if len(csi)>=4 and (re.search('^1,',line) or re.search('^15,',line)):
            # print line
            # correct 2400 hour
            # get sample datetime from data
            yyyy = csi[1]
            yday = csi[2]
            (MM, HH) = math.modf(csi[3]/100.)
            MM = math.ceil(MM*100.)
            if (HH == 24):
                yday=yday+1
                HH = 0.
            
            sample_str = '%04d-%03d %02d:%02d' % (yyyy, yday, HH, MM)
            sample_dt = scanf_datetime(sample_str, fmt='%Y-%j %H:%M')
            month_str = '%4d_%02d' % sample_dt.timetuple()[0:2]
        else:
            # not a well-formed line, so skip to next line
            print 'ill-formed time, line not to be copied: ' + line
            continue

        if re.search('^1,',line) and len(csi)>=4:
            # does month dir exist
            data_dir = os.path.join(p[0],'wq',month_str)

            if not os.path.isdir(data_dir):
                print 'Creating directory: '+data_dir
                os.mkdir(data_dir)
                
            ofn_prefix = '%s_%s' % (id, 'wq')
            ofn = os.path.join(data_dir, ofn_prefix)
            ofn = '_'.join([ofn, month_str])
            ofn = '.'.join([ofn, 'dat'])
                
            if os.path.exists(ofn):
                f = open(ofn, 'a')
                f.write(line)
                f.close
            else:
                print 'Creating file: '+ofn
                f = open(ofn, 'w')
                f.write(line)
                f.close()

        if re.search('^15,',line) and len(csi)>=4:
            data_dir = os.path.join(p[0],'flow',month_str)

            if not os.path.isdir(data_dir):
                print 'Creating directory: '+data_dir
                os.mkdir(data_dir)
                
            ofn_prefix = '%s_%s' % (id, 'flow')
            ofn = os.path.join(data_dir, ofn_prefix)
            ofn = '_'.join([ofn, month_str])
            ofn = '.'.join([ofn, 'dat'])
                
            if os.path.exists(ofn):
                f = open(ofn, 'a')
                f.write(line)
                f.close
            else:
                print 'Creating file: '+ofn
                f = open(ofn, 'w')
                f.write(line)
                f.close()
        
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

    # data prior to 2009-01 (CR10X v1 and v2)
    fns = [
        '/seacoos/data/nccoos/level0/crow/cbc_loggernet_20060316-20080829.dat',
        #
        '/seacoos/data/nccoos/level0/meet/mow_loggernet_20010510-20030925.dat',
        '/seacoos/data/nccoos/level0/meet/mow_loggernet_20030925-20041209.dat',
        '/seacoos/data/nccoos/level0/meet/mow_loggernet_20050325-20070726.dat',
        '/seacoos/data/nccoos/level0/meet/mow_loggernet_20080404-20080826.dat',
        ]

    for fn in fns:
        test1(fn)


if __name__ == '__main__':
    pass
#    fn = '/seacoos/data/nccoos/level0/crow/cbc_loggernet_20050325-20070726.dat'
#
#    # 
#    # fn = sys.argv[1]
#    try:
#        test1(fn)
#    except:
#        pass
    
