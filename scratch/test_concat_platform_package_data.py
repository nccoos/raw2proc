#!/usr/bin/env python
# Last modified:  Time-stamp: <2008-10-22 13:14:19 haines>
"""test_concat_data"""

import os, sys, glob
import datetime, time, dateutil, dateutil.tz
import pycdf
import numpy

sys.path.append('/home/haines/nccoos/raw2proc')
del(sys)

import procutil

# test with jpier adcp
# proc_dir ='/seacoos/data/nccoos/level1/jpier/adcp/'
# proc_dir ='/seacoos/data/nccoos/level1/bogue/adcp/'
proc_dir ='/seacoos/data/nccoos/level1/lsrb/adcp/'
fns = glob.glob((os.path.join(proc_dir, '*.nc')))
fns.sort()

# pick which months cover deployment 
nc = pycdf.CDFMF(fns[16:18])

ncvars = nc.variables()
# print ncvars
es = nc.var('time')[:]
units = nc.var('time').units
dt = [procutil.es2dt(e) for e in es]
# set timezone info to UTC (since data from level1 should be in UTC!!)
dt = [e.replace(tzinfo=dateutil.tz.tzutc()) for e in dt]
# return new datetime based on computer local
dt_local = [e.astimezone(dateutil.tz.tzlocal()) for e in dt]
z = nc.var('z')[:]
wd = nc.var('wd')[:]
u = nc.var('u')[:]
v = nc.var('v')[:]
nc.close()


# averaged water depth over whole recorded deployment!!
print wd.mean()
