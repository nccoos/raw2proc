#!/usr/bin/env python
# Last modified:  Time-stamp: <2011-02-16 16:32:33 haines>
"""
parse ascii text file of YSI 6600 V2 water quality data (.dat)

load data file
parse data into variables for appending to netCDF data

water depth is read from the file but stored in separate netCDF
because of different sample interval

"""

REAL_RE_STR = '\\s*(-?\\d(\\.\\d+|)[Ee][+\\-]\\d\\d?|-?(\\d+\\.\\d*|\\d*\\.\\d+)|-?\\d+)\\s*'

import sys
import os
import re

def parse_avp_YSI_6600V2(fn, lines):
    """
    parse Automated Vertical Profile Station (AVP) Water Quality Data

    month, day, year, hour, min, sec, temp (deg. C), conductivity
    (mS/cm), salinity (ppt or PSU), depth (meters), pH, turbidity (NTU),
    chlorophyll (micrograms per liter), DO (micrograms per liter)

    Notes
    -----
    1. Column Format

    temp, cond, salin, depth, pH, turb, chl, DO
    (C), (mS/cm), (ppt), (m), pH, (NTU), (ug/l), (ug/l)

    Profile Time: 00:30:00
    Profile Date: 08/18/2008
    Profile Depth: 255.0 cm
    Profile Location: Stones Bay Serial No: 00016B79, ID: AVP1_SERDP
    08/18/08 00:30:06 26.94  41.87  26.81   0.134  8.00     3.4   4.5   6.60
    08/18/08 00:30:07 26.94  41.87  26.81   0.143  8.00     3.4   4.8   6.59
    08/18/08 00:30:08 26.94  41.87  26.81   0.160  8.00     3.4   4.8   6.62
    08/18/08 00:30:09 26.94  41.87  26.81   0.183  8.00     3.4   4.8   6.66

    2. read each sample and create timeseries for each parameter along
       with the recorded depth of each sample, z(t)

    """
    import numpy
    from datetime import datetime
    from time import strptime

    # get sample datetime from filename
    # fn = sensor_info['fn']
    sample_dt_start = filt_datetime(fn)[0]

    # how many samples
    nsamp = 0
    for line in lines:
        m=re.search("^\d{2}\/\d{2}\/\d{2}", line)
        if m:
            nsamp=nsamp+1

    N = nsamp
    data = {
        'dt' : numpy.array(numpy.ones((N,), dtype=object)*numpy.nan),
        'time' : numpy.array(numpy.ones((N,), dtype=long)*numpy.nan),
        'wtemp' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'cond' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'salin' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'depth' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'turb' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'ph' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'chl' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'do' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        }

    # sample count
    i = 0

    for line in lines:
        ysi = []
        # split line and parse float and integers
        sw = re.split('[\s/\:]*', line)
        for s in sw:
            m = re.search(REAL_RE_STR, s)
            if m:
                ysi.append(float(m.groups()[0]))

        if len(ysi)==14:                                                                             
            # get sample datetime from data
            sample_str = '%02d-%02d-%2d %02d:%02d:%02d' % tuple(ysi[0:6])
            # if  sensor_info['utc_offset']:
            #     sample_dt = scanf_datetime(sample_str, fmt='%m-%d-%Y %H:%M:%S') + \
            #                 timedelta(hours=sensor_info['utc_offset'])
            # else:
            sample_dt = scanf_datetime(sample_str, fmt='%m-%d-%y %H:%M:%S')

            wtemp[i] = ysi[6] # water temperature (C)
            cond[i]  = ysi[7] # conductivity (mS/cm)
            salin[i] = ysi[8] # salinity (ppt or PSU??)
            depth[i] = ysi[9] # depth (m) 
            #
            ph[i] = ysi[10]   # ph
            turb[i] = ysi[11] # turbidity (NTU)
            chl[i] = ysi[12]  # chlorophyll (ug/l)
            do[i] = ysi[13]   # dissolved oxygen (ug/l)

            data['dt'][i] = sample_dt # sample datetime
            data['time'][i] = dt2es(sample_dt) # sample time in epoch seconds
            # 
            data['wtemp'][i] =  wtemp
            data['cond'][i] = cond
            data['salin'][i] = salin
            data['depth'][i] = depth
            data['turb'][i] = turb
            data['ph'][i] = ph
            data['chl'][i] = chl
            data['do'][i] = do
            
            i=i+1

        # if-elif
    # for line

    return data
    

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

# from jpier_config_20080411 import *
from raw2proc import *

def test1(fn):
    lines = load_data(fn)
    return parse_avp_YSI_6600V2(fn, lines)

def test2(logFile):
    pi = get_config('stones_config_YYYYMMDD.platform_info')
    asi = get_config('stones_config_YYYYMMDD.sensor_info')
    si = asi['met']
    lines = load_data(logFile)
    si['fn'] = logFile
    (parse, create, update) = import_processors(si['process_module'])
    return parse(pi, si, logFile)

if __name__ == '__main__':
    fn = '/seacoos/data/nccoos/level0/stones/avp/2008_08/AVP1_20080811.dat'
    # dataFile = 'D:/haines/nc-coos/raw2proc/stones/met/2008_08/AVP1_20080811.wnd'

    # logFile = sys.argv[1]
    try:
        data = test1(fn)
    except:
        pass
    
