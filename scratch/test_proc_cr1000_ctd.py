#!/usr/bin/env python
# Last modified:  Time-stamp: <2012-06-28 14:36:45 haines>

import sys
import os
import re
from procutil import *
from raw2proc import *

import numpy
from datetime import datetime
from time import strptime

fn = '/seacoos/data/nc-coos/level0/b1/ctd1/2011_11/b1_ctd1_2011_11.dat'
lines = load_data(fn)

now_dt = datetime.utcnow()
now_dt.replace(microsecond=0)

cn = 'b1_config_20111112'
platform_info = get_config(cn+'.platform_info')
asi = get_config(cn+'.sensor_info')
sensor_info = asi['ctd1']



def parser(platform_info, sensor_info, lines):
    """
    "TOA5","CR1000_B1","CR1000","37541","CR1000.Std.21","CPU:NCWIND_12_Buoy_All.CR1","58723","CTD1_6Min"
    "TIMESTAMP","RECORD","ID","Temp","Cond","Depth","SampleDate","SampleTime","SampleNum"
    "TS","RN","","","","","","",""
    "","","Smp","Smp","Smp","Smp","Smp","Smp","Smp"
    "2011-12-01 00:02:09",4449,3585,16.1596,4.15704,3.413," 30 Nov 2011"," 23:58:44","   4406 "
    "2011-12-01 00:08:09",4450,3585,16.1783,4.15878,3.745," 01 Dec 2011"," 00:04:44","   4407 "
    "2011-12-01 00:14:09",4451,3585,16.1638,4.15794,3.545," 01 Dec 2011"," 00:10:44","   4408 "
    "2011-12-01 00:20:09",4452,3585,16.1632,4.15769,3.254," 01 Dec 2011"," 00:16:44","   4409 "
    "2011-12-01 00:26:09",4453,3585,16.1524,4.15665,3.649," 01 Dec 2011"," 00:22:44","   4410 "
    "2011-12-01 00:32:09",4454,3585,16.1661,4.1582,3.277," 01 Dec 2011"," 00:28:44","   4411 "
    """

    import numpy
    from datetime import datetime
    from time import strptime

    # how many samples (don't count header 4 lines)
    nsamp = len(lines[4:])

    N = nsamp
    data = {
        'dt' : numpy.array(numpy.ones((N,), dtype=object)*numpy.nan),
        'time' : numpy.array(numpy.ones((N,), dtype=long)*numpy.nan),
        'wtemp' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'cond' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'press' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'salin' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'density' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'depth' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        }

    # sample count
    i = 0

    for line in lines[4:]:
        csi = []
        # split line
        sw = re.split(',', line)
        if len(sw)<=0:
            print ' ... skipping line %d ' % (i,)
            continue

        # replace "NAN"
        for index, s in enumerate(sw):
            m = re.search(NAN_RE_STR, s)
            if m:
                sw[index] = '-99999'

        # parse date-time, and all other float and integers
        for s in sw[1:6]:
            m = re.search(REAL_RE_STR, s)
            if m:
                csi.append(float(m.groups()[0]))

        # if no proper date/time from CTD, move on to next line
        dstr = re.sub('"', '', sw[6]+' '+sw[7])        
        m = re.search('\s*(\d{2})\s*(\w{2,3})\s*(\d{4})\s*(\d{2}):(\d{2}):(\d{2})', dstr)
        if m:
            dstr = '%s %s %s %s:%s:%s' % m.groups()
        else:
            print ' ... skipping line %d -- %s ' % (i,line)
            continue            
            
        if  sensor_info['utc_offset']:
            sample_dt = scanf_datetime(dstr, fmt='%d %b %Y %H:%M:%S') + \
                        timedelta(hours=sensor_info['utc_offset'])
        else:
            sample_dt = scanf_datetime(dstr, fmt='%d %b %Y %H:%M:%S')

        # ***** TO DO: need to adjust any drift of offset in CTD sample time to CR1000 clock
        data['dt'][i] = sample_dt # sample datetime
        data['time'][i] = dt2es(sample_dt) # sample time in epoch seconds

        if len(csi)==5:
            #
            sn = csi[1] # ctd serial number == check against platform configuration
            data['wtemp'][i] =  csi[2] # water temperature (C)
            data['cond'][i] = csi[3] # specific conductivity (S/m)
            data['press'][i] = csi[4]   # pressure decibars
            i=i+1
        else:
            print ' ... skipping line %d -- %s ' % (i,line)
            continue            
            

        # if re.search
    # for line


    # check that no data[dt] is set to Nan or anything but datetime
    # keep only data that has a resolved datetime
    keep = numpy.array([type(datetime(1970,1,1)) == type(dt) for dt in data['dt'][:]])
    if keep.any():
        for param in data.keys():
            data[param] = data[param][keep]

    # QC before
    good = (5<data['wtemp']) & (data['wtemp']<30)
    bad = ~good
    data['wtemp'][bad] = numpy.nan 

    good = (2<data['cond']) & (data['cond']<7)
    bad = ~good
    data['cond'][bad] = numpy.nan 

    # calculate depth, salinity and density
    import seawater.csiro
    data['depth'] = -1*seawater.csiro.depth(data['press'], platform_info['lat'])  # meters
    data['salin'] = seawater.csiro.salt(10*data['cond']/seawater.constants.C3515, data['wtemp'], data['press']) 
    data['density'] = seawater.csiro.dens(data['salin'], data['wtemp'], data['press']) 

    return data


    
