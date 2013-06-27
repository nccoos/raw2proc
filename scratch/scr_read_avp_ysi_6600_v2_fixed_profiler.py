#!/usr/bin/env python
# Last modified:  Time-stamp: <2008-09-09 12:56:46 haines>
"""
parse ascii text file of YSI 6600 V2 water quality data (.dat)

load data file
parse data into variables for appending to netCDF data

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

    2. While each parameter is measured uniquely with time and depth such that, temp(t) and z(t)
    match up with time, we want to grid depth every 1 cm and make each param as temp(t,z).

    Tony Whipple at IMS says 'The AVPs sample at one second intervals.
    Between the waves and the instrument descending from a spool of
    line with variable radius it works out to about 3-5 cm between
    observations on average.  When I process the data to make the
    images, I bin the data every 10 cm and take the average of however
    many observations fell within that bin.'

    Do we interpolate or average samples in bin? 

    """
    import numpy
    from datetime import datetime
    from time import strptime

    # get sample datetime from filename
    # fn = sensor_info['fn']
    sample_dt_start = filt_datetime(fn)[0]

    # how many profiles in one file, count number of "Profile Time:" in lines
    nprof = 0
    for line in lines:
        m=re.search("Profile Time:", line)
        if m:
            nprof=nprof+1

    # remove first occurrence of blank line if within first 10-40 lines
    # and put it on the end to signal end of profile after last profile
    for i in range(len(lines[0:40])):
        if re.search("^ \r\n", lines[i]):
            # print str(i) + " " + lines[i] + " " + lines[i+1]
            blank_line = lines.pop(i)
    lines.append(blank_line)
    
    bin_size = 0.1 # 10cm or 0.1m
    z = numpy.arange(0,4.0,bin_size,dtype=float)
    
    N = nprof
    nbins = len(z)
    data = {
        'dt' : numpy.array(numpy.ones((N,), dtype=object)*numpy.nan),
        'time' : numpy.array(numpy.ones((N,), dtype=long)*numpy.nan),
        'water_depth' : numpy.array(numpy.ones((N,), dtype=long)*numpy.nan),
        'wtemp' : numpy.array(numpy.ones((N,nbins), dtype=float)*numpy.nan),
        'cond' : numpy.array(numpy.ones((N,nbins), dtype=float)*numpy.nan),
        'salin' : numpy.array(numpy.ones((N,nbins), dtype=float)*numpy.nan),
        'turb' : numpy.array(numpy.ones((N,nbins), dtype=float)*numpy.nan),
        'ph' : numpy.array(numpy.ones((N,nbins), dtype=float)*numpy.nan),
        'chl' : numpy.array(numpy.ones((N,nbins), dtype=float)*numpy.nan),
        'do' : numpy.array(numpy.ones((N,nbins), dtype=float)*numpy.nan),
        }

    # current profile count
    i = 0 

    for line in lines:
        ysi = []
        # split line and parse float and integers
        sw = re.split('[\s/\:]*', line)
        for s in sw:
            m = re.search(REAL_RE_STR, s)
            if m:
                ysi.append(float(m.groups()[0]))

        if re.search("Profile Time:", line):
            HH=ysi[0]
            MM=ysi[1]
            SS=ysi[2]

        elif re.search("Profile Date:", line):
            dd=ysi[0]
            mm=ysi[1]
            yyyy=ysi[2]

        elif re.search("Profile Depth:", line):
            water_depth = ysi[0]/100.  # cm to meters
            sample_str = '%02d-%02d-%d %02d:%02d:%02d' % (mm,dd,yyyy,HH,MM,SS)
            # if  sensor_info['utc_offset']:
            #     sample_dt = scanf_datetime(sample_str, fmt='%m-%d-%Y %H:%M:%S') + \
            #                 timedelta(hours=sensor_info['utc_offset'])
            # else:
            sample_dt = scanf_datetime(sample_str, fmt='%m-%d-%Y %H:%M:%S')
                                                                        
            # initialize for new profile at zero for averaging samples within each bin
            wtemp = numpy.zeros(nbins)
            cond = numpy.zeros(nbins)
            salin = numpy.zeros(nbins)
            turb = numpy.zeros(nbins)
            ph = numpy.zeros(nbins)
            chl = numpy.zeros(nbins)
            do = numpy.zeros(nbins)

            Ns = numpy.zeros(nbins) # count samples per bin for averaging

        elif len(ysi)==14:                                                                             
            # get sample datetime from data
            # sample_str = '%02d-%02d-%2d %02d:%02d:%02d' % tuple(ysi[0:6])
            # if  sensor_info['utc_offset']:
            #     sample_dt = scanf_datetime(sample_str, fmt='%m-%d-%Y %H:%M:%S') + \
            #                 timedelta(hours=sensor_info['utc_offset'])
            # else:
            # sample_dt = scanf_datetime(sample_str, fmt='%m-%d-%y %H:%M:%S')

            depth = ysi[9] # depth (m)
            ibin = ((z)<=depth)*(depth<(z+bin_size))

            Ns[ibin] = Ns[ibin]+1
            wtemp[ibin] = wtemp[ibin]+ysi[6] # water temperature (C)
            cond[ibin] = cond[ibin]+ysi[7]   # conductivity (mS/cm)
            salin[ibin] = salin[ibin]+ysi[8] # salinity (ppt or PSU??)
            #
            ph[ibin] = ph[ibin]+ysi[10]      # ph
            turb[ibin] = turb[ibin]+ysi[11]  # turbidity (NTU)
            chl[ibin] = chl[ibin]+ysi[12]    # chlorophyll (ug/l)
            do[ibin] = do[ibin]+ysi[13]      # dissolved oxygen (ug/l)

        elif (len(ysi)==0):
            # average summations by sample count per bin
            # where count is zero make it NaN so average is not divide by zero
            Ns[Ns==0]=numpy.nan*Ns[Ns==0]
            
            data['dt'][i] = sample_dt # sample datetime
            data['time'][i] = dt2es(sample_dt) # sample time in epoch seconds
            data['water_depth'][i] = water_depth
            # divide by counts 
            data['wtemp'][i] =  wtemp/Ns
            data['cond'][i] = cond/Ns
            data['salin'][i] = salin/Ns
            data['turb'][i] = turb/Ns
            data['ph'][i] = ph/Ns
            data['chl'][i] = chl/Ns
            data['do'][i] = do/Ns
            
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
    
