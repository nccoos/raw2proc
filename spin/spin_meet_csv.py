#!/usr/bin/env python
# Last modified:  Time-stamp: <2009-12-07 16:43:48 haines>
"""spin_meet_csv"""

# create csv files from netcdf

import os, sys, glob, re
import datetime, time, dateutil, dateutil.tz
import pycdf
import numpy
import csv

sys.path.append('/opt/env/haines/dataproc/raw2proc')
import procutil
del(sys)

print 'spin_meet_csv ...'

proc_dir = '/seacoos/data/nccoos/level1/meet/wq'
fns = glob.glob((os.path.join(proc_dir, '*.nc')))
# fns = glob.glob((os.path.join(proc_dir, '*2009*.nc')))
fns.sort()

for fn in fns:
    m=re.search('\d{4}_\d{2}', fn)
    yyyy_mm = m.group()
    prev_month, this_month, next_month = procutil.find_months(yyyy_mm)
    yyyy_mm_str = this_month.strftime('%Y_%m')
    
    # load data
    print ' ... ... read: ' + fn
    nc = pycdf.CDFMF((fn,))
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
    wtemp = nc.var('wtemp')[:]
    cond = nc.var('cond')[:]
    turb = nc.var('turb')[:]
    ph = nc.var('ph')[:]
    do_mg = nc.var('do_mg')[:]
    do_sat = nc.var('do_sat')[:]
    batt = nc.var('battvolts')[:]
    nc.close()
    
    # save csv    
    ofn = proc_dir + '_csv/meet_wq_' + yyyy_mm_str + '.csv'
    print '... ... write: %s' % (ofn,)

    ofp = open(ofn, 'w')
    csvwriter = csv.writer(ofp, dialect='excel', quoting=csv.QUOTE_NONNUMERIC)
    csvwriter.writerow(['TOA5','MOW','CPU:UNC_MeetingWaters','DataHourly'])
    csvwriter.writerow(['TIMESTAMP','SondeTempC','SpCond','DOSat','DOmg','pH','Turb','BattVolt_Min'])
    csvwriter.writerow(['TS','','','','','','',''])
    csvwriter.writerow(['','Smp','Smp','Smp','Smp','Smp','Smp','Min'])

    fmt = '%Y-%m-%d %H:%M:%S'
    for i in range(len(dt)):
        row = [dt[i].strftime(fmt), wtemp[i],cond[i],do_sat[i],do_mg[i],ph[i],turb[i],batt[i]]
        csvwriter.writerow(row)
    ofp.close()



proc_dir = '/seacoos/data/nccoos/level1/meet/flow'
fns = glob.glob((os.path.join(proc_dir, '*.nc')))
# fns = glob.glob((os.path.join(proc_dir, '*2009*.nc')))
fns.sort()
for fn in fns:
    m=re.search('\d{4}_\d{2}', fn)
    yyyy_mm = m.group()
    prev_month, this_month, next_month = procutil.find_months(yyyy_mm)
    yyyy_mm_str = this_month.strftime('%Y_%m')

    print ' ... ... read: ' + fn
    nc = pycdf.CDFMF((fn,))
    ncvars = nc.variables()
    # print ncvars
    es = nc.var('time')[:]
    units = nc.var('time').units
    dt = [procutil.es2dt(e) for e in es]
    # set timezone info to UTC (since data from level1 should be in UTC!!)
    dt = [e.replace(tzinfo=dateutil.tz.tzutc()) for e in dt]
    
    rain = nc.var('rain')[:] # inches of rain in past 15 min
    # all sontek data at Meeting of the Waters is suspicious and not to be used.
    have_sontek = False
    # have_sontek = 'sontek_wl' in ncvars.keys() or 'sontek_flow' in ncvars.keys()
    pwl = nc.var('press_wl')[:] # feet
    pfl = nc.var('press_flow')[:] # cfs
    
    if have_sontek:
        swl = nc.var('sontek_wl')[:] # feet
        sfl = nc.var('sontek_flow')[:] # cfs
    
    nc.close()

    # save csv    
    ofn = proc_dir + '_csv/meet_flow_' + yyyy_mm_str + '.csv'
    print '... ... write: %s' % (ofn,)

    ofp = open(ofn, 'w')
    csvwriter = csv.writer(ofp, dialect='excel', quoting=csv.QUOTE_NONNUMERIC)
    csvwriter.writerow(['TOA5','MOW','CPU:UNC_MeetingWaters','Data15Min'])

    if have_sontek:
        csvwriter.writerow(['TIMESTAMP','Rain INCHES',
                            'Press Water Level UNITS?','Press Flow CFS',
                            'SONTEK Water Level FEET','SONTEK Flow CFS'])
        csvwriter.writerow(['TS','','','','','',''])
        csvwriter.writerow(['','Smp','Smp','Smp','Smp','Smp'])

        fmt = '%Y-%m-%d %H:%M:%S'
        for i in range(len(dt)):
            row = [dt[i].strftime(fmt), rain[i], pwl[i], pfl[i], swl[i], sfl[i]]
            csvwriter.writerow(row)

    else:
        csvwriter.writerow(['TIMESTAMP','Rain INCHES',
                            'Press Water Level FEET','Press Flow CFS'])
        csvwriter.writerow(['TS','','','',''])
        csvwriter.writerow(['','Smp','Smp','Smp'])

        fmt = '%Y-%m-%d %H:%M:%S'
        for i in range(len(dt)):
            row = [dt[i].strftime(fmt), rain[i], pwl[i], pfl[i]]
            csvwriter.writerow(row)

    ofp.close()
