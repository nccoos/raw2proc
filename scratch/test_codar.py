#!/usr/bin/env python
# Last modified:  Time-stamp: <2010-12-09 16:17:25 haines>

import sys
import os
import re
from procutil import *
from raw2proc import *

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

import numpy
from datetime import datetime
from time import strptime
from StringIO import StringIO
from matplotlib.mlab import griddata

fn = '/seacoos/data/nc-coos/level0/ouba/hfr_totals/2010_07/TOTL_OUBA_2010_07_14_0000.tuv'
lines = load_data(fn)

# get sample datetime from filename
# fn = sensor_info['fn']
# sample_dt_start = filt_datetime(fn)

# read header that match '%(k): (v)\n' pairs on each line
m = re.findall(r'^(%.*):\s*(.*)$', ''.join(lines), re.MULTILINE)
for k,v in m:
    if k == '%TimeStamp':
        sample_dt = scanf_datetime(v, fmt='%Y %m %d %H %M %S')
    elif k == '%TableType':
        ftype = v
    elif k == '%TableColumns':
        ncol = int(v)
    elif k == '%TableRows':
        nrow = int(v)

# read data from string of lines but make it behave like a file object with StringIO
s = StringIO(''.join(lines))
s.seek(0) # ensures start posn of file
d = numpy.loadtxt(s, comments='%')
# lat, lon, u, v = numpy.loadtxt(s, usecols=(0,1,2,3), comments='%', unpack=True)
if 'TOT4' in ftype:
    lon = d[:,0]
    lat = d[:,1]
    wu = d[:,2]
    wv = d[:,3]
    gridflag = d[:,4]
    wu_std_qual = d[:,5]
    wv_std_qual = d[:,6]
    cov_qual = d[:,7]
    x_dist = d[:,8]
    y_dist = d[:,9]
    rang = d[:,10]
    bearing = d[:,11]
    vel_mag = d[:,12]
    vel_dir = d[:,13]
    s1 = d[:,14]
    s2 = d[:,15]
    s3 = d[:,16]
    s4 = d[:,17]
    s5 = d[:,18]
    s6 = d[:,19]

# define the lat/lon grid based on 6km resolution
# For Outer Banks north and east of Cape Hatteras, bounding box is defined by:
minlat, maxlat = (34.5, 38)
minlon, maxlon = (-76, -73.)
midlat = minlat + 0.5*(maxlat-minlat)
# ~111 km = 1 deg latitude
nlat = numpy.round((maxlat-minlat) *111/6)
nlon = numpy.round((maxlon-minlon) * math.cos(midlat*math.pi/180)*111/6)
yi = numpy.linspace(minlat, maxlat, nlat)
xi = numpy.linspace(minlon, maxlon, nlon)
ui = griddata(lon, lat, wu, xi, yi)
vi = griddata(lon, lat, wv, xi, yi)
# ---------------------------------------------------------------
data = {
    'dt' : numpy.array(numpy.ones((1,), dtype=object)*numpy.nan),
    'time' : numpy.array(numpy.ones((1,), dtype=long)*numpy.nan),
    'lon' : numpy.array(numpy.ones((1,nlon), dtype=float)*numpy.nan),
    'lat' : numpy.array(numpy.ones((1,nlat), dtype=float)*numpy.nan),
    'u' : numpy.array(numpy.ones((1,nlon,nlat), dtype=float)*numpy.nan),
    'v' : numpy.array(numpy.ones((1,nlon,nlat), dtype=float)*numpy.nan),
    }
# ---------------------------------------------------------------
i = 0
data['dt'][i] =  sample_dt # 
data['time'][i] =  dt2es(sample_dt) # 
data['lon'][i] = xi # new longitude grid
data['lat'][i] = yi # new latitude grid
data['u'][i] = ui # u-component of water velocity (cm/s)
data['v'][i] = vi # v-component of water velocity 



    
