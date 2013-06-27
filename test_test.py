#!/usr/bin/env python

from raw2proc import *

# fn = '/seacoos/data/nc-coos/level0/ouba/hfr_totals/2013_04/TOTL_OUBA_2013_04_25_1000.tuv'
fn = '/seacoos/data/nc-coos/level0/ouba/hfr_totals/2013_04/TOTL_OUBA_2013_04_26_1600.tuv'
lines = load_data(fn)

import sys
import os
import re
from procutil import *

import numpy
from datetime import datetime
from time import strptime
from StringIO import StringIO
from matplotlib.mlab import griddata

# get sample datetime from filename
# fn = sensor_info['fn']
sample_dt_start = filt_datetime(fn)
fn_dt_str = sample_dt_start.strftime("%Y_%m_%d_%H%M")

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

# define the lat/lon grid based on 6km resolution
# For Outer Banks north and east of Cape Hatteras, bounding box is defined by:
minlat, maxlat = (34.5, 38)
minlon, maxlon = (-76, -73.)
midlat = minlat + 0.5*(maxlat-minlat)
# ~111 km = 1 deg latitude
nlat = 65
nlon = 45
yi = numpy.linspace(minlat, maxlat, nlat)
xi = numpy.linspace(minlon, maxlon, nlon)
xmesh, ymesh = numpy.meshgrid(xi,yi)

# ibad = (wu_std_qual==999.) | (wv_std_qual==999.) | (cov_qual==999.)
# wu[ibad] = numpy.nan
# wv[ibad] = numpy.nan

uim = griddata(lon, lat, wu, xmesh, ymesh)
vim = griddata(lon, lat, wv, xmesh, ymesh)
# returned masked array as an ndarray with masked values filled with fill_value
ui = uim.filled(fill_value=numpy.nan)
vi = vim.filled(fill_value=numpy.nan)

# want to visualize this using matplotlib
os.environ["MPLCONFIGDIR"]="/home/haines/.matplotlib/"
from pylab import figure, twinx, twiny, savefig, setp, getp, cm, colorbar
fig = figure(figsize=(9, 7))

#######################################
# lat, lon and xi, yi
#######################################
ax = fig.add_axes((.1,.4,.4,.45))
axs = [ax]

ax.scatter(lon,lat,marker='o',c='b',s=5,zorder=10)
ax.scatter(xmesh,ymesh,marker='x',c='r',s=5,zorder=10)

# use masked array to hide NaN's on plot
# Sxxm = numpy.ma.masked_where(Sxx==0.0, Sxx)
# pc = ax.pcolor(f, d, Sxxm.T, vmin=cmin, vmax=cmax)
# pc = ax.pcolor(f, d, Sxxm.T)
ax.set_ylabel('Latitude (deg N)')
ax.set_ylim(minlat, maxlat)
ax.set_xlabel('Longitude (deg W)')
ax.set_xlim(minlon, maxlon)


# save figure
ofn = os.path.join('/home/haines/rayleigh/img/hfr', 'totals_'+fn_dt_str+'.png')
savefig(ofn)
                                                                                                    
############################################
m = re.findall(r'^(%.*):\s*(.*)$', ''.join(lines), re.MULTILINE)
for k,v in m:
    if k == '%TimeStamp':
        sample_dt = scanf_datetime(v, fmt='%Y %m %d %H %M %S')
    elif k == '%TableType':
        ftype = v
    elif k == '%LLUVSpec':
        lluvspec = float(re.split('\s+', v)[0])
    elif k == '%TableColumns':
        ncol = int(v)
    elif k == '%TableRows':
        nrow = int(v)
    elif k == '%TableEnd':
        break

