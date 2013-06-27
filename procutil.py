#!/usr/bin/env python
# Last modified:  Time-stamp: <2012-05-15 10:51:49 haines>
"""Utilities to help data processing 

   Mostly time functions right now

"""

__version__ = "v0.1"
__author__ = "Sara Haines <sara_haines@unc.edu>"

import os.path
from datetime import datetime, timedelta, tzinfo
from dateutil.tz import tzlocal, tzutc
from dateutil.parser import parse
import time
import math

from ncutil import *

def check_configs():
    """Test config files for comformnity

    check either one or all for a platform
    
    id in filename == platform.id
    datetime in filename <= platform.config_start_date
       (close in time usually the same day
    also platform.config_start_date < platform.config_end_date
       (there needs to be some time that the platform was operational)
    test existence of specific structural elements (platform info and sensor info)
    and specific fields for both platform and sensor
    verify that for each platform_info['packages'] there is sensor_info and same id
      for pi['packages'][0] in si.keys()
      pi['packages'][0] == si['adcp']['id']
    bounds on data in fields
    show difference between two consecutive configs?
    pretty print to screen of dictionary info for platform and sensor info
    
        cn = os.path.splitext(os.path.basename(config))[0]
        cndt = filt_datetime(os.path.basename(config))
        pi = get_config(cn+'.platform_info')
        if pi['config_start_date']:
            config_start_dt = filt_datetime(pi['config_start_date'])
        elif pi['config_start_date'] == None:
            config_start_dt = now_dt
        if pi['config_end_date']:
            config_end_dt = filt_datetime(pi['config_end_date'])
        elif pi['config_end_date'] == None:
            config_end_dt = now_dt

        print cn + ' -----------------'
        print cndt
        print config_start_dt
        print config_end_dt 
        print now_dt
        print 'file date ok? ' + str(cndt <= config_start_dt)
        print 'operation date ok? ' + str(config_start_dt < config_end_dt)
    """

def dt2es(dt):
    """Convert datetime object to epoch seconds (es) as seconds since Jan-01-1970 """
    # microseconds of timedelta object not used
    delta = dt - datetime(1970,1,1,0,0,0)
    es = delta.days*24*60*60 + delta.seconds
    return es 

def es2dt(es):
    """ Convert epoch seconds (es) to datetime object"""
    dt = datetime(*time.gmtime(es)[0:6])
    return dt

def find_months(year, month=1):
    """Find which months to process

    Since data are in subdirectories based on months determine
    previous, current, and next month to look in directories for data
    of the current month or month to process.

    :Parameters:
        year : int value or str 'yyyy_mm'
        month : int value

    :Returns:
        which_months : tuple of 3 datetime objects
             (prev_month, current_month, next_month)

    Examples
    --------
    >>> find_months(2007, 2)
    >>> find_months('2007_02')
    
    """
    if type(year) == int and type(month) == int :
        dt = datetime(year, month, day=1)
        this_month = dt
    elif type(year) == str :
        dt = filt_datetime(year)
        this_month = dt
    #
    if dt.month == 1: # if January
        prev_month = datetime(dt.year-1, month=12, day=1) # Dec
        next_month = datetime(dt.year, dt.month+1, day=1) # Feb
    elif dt.month == 12: # if December
        prev_month = datetime(dt.year, dt.month-1, day=1) # Nov
        next_month = datetime(dt.year+1, month=1, day=1)  # Jan
    else:
        prev_month = datetime(dt.year, dt.month-1, day=1)
        next_month = datetime(dt.year, dt.month+1, day=1)
    #
    return (prev_month, this_month, next_month)

def this_month():
    """Return this month (GMT) as formatted string (yyyy_mm) """
    this_month_str = "%4d_%02d" % time.gmtime()[0:2]
    return this_month_str

def scanf_datetime(ts, fmt='%Y-%m-%dT%H:%M:%S'):
    """Convert string representing date and time to datetime object"""
    # default string format follows convention YYYY-MM-DDThh:mm:ss
    
    try:
        t = time.strptime(ts, fmt)
        # the '*' operator unpacks the tuple, producing the argument list.
        dt = datetime(*t[0:6])
    except ValueError, e:
        # value error if something not valid for datetime
        # e.g. month 1...12, something parsed wrong
        dt = None
    # else:
    #    # absolute difference in days from now (UTC)
    #     z = dt - datetime.utcnow()
    #     daysdiff = abs(z.days)
    #     # if this date unreasonable (>10 years*365), throw it out
    #     # something parsed wrong
    #     if daysdiff > 3650:
    #         dt = None                

    return dt

def filt_datetime_test(input_string, remove_ext=True):
    """
    Following the template, (YY)YYMMDDhhmmss
    and versions with of this with decreasing time precision,
    find the most precise, reasonable string match and
    return its datetime object.
    """

    from dateutil.parser import parse

    # remove any trailing filename extension
    from os.path import splitext
    import re
    if remove_ext:
        (s, e) = splitext(input_string)
        input_string = s

    try:
        dt = parse(input_string, fuzzy=True)
    except ValueError, e:
        print 'filt_datetime: Could not parse date. No date found in ', input_string
        dt = None
    else:
        return dt




def filt_datetime(input_string, gran=False, remove_ext=True):
    """
    Following the template, (YY)YYMMDDhhmmss
    and versions with of this with decreasing time precision,
    find the most precise, reasonable string match and
    return its datetime object.

    gran=False don't return granularity number
    
    
    """

    # remove any trailing filename extension
    from os.path import splitext
    import re
    if remove_ext:
        (s, e) = splitext(input_string)
        input_string = s
    
    # YYYYMMDDhhmmss and should handle most cases of the stamp
    # other forms this should pass
    # YY_MM_DD_hh:mm:ss
    # YYYY_MM_DD_hh:mm:ss
    # YYYY,MM,DD,hh,mm,ss
    # YY,MM,DD,hh,mm,ss

    case1_regex = r"""
    # case 1: YYYYMMDDhhmmss 
    (\d{4})     # 2- or 4-digit YEAR (e.g. '07' or '2007')
    \D?               # optional 1 character non-digit separator (e.g. ' ' or '-')
    (\d{2})           # 2-digit MONTH (e.g. '12')
    \D?               # optional 1 character non-digit separator
    (\d{2})           # 2-digit DAY of month (e.g. '10')
    \D?               # optional 1 character non-digit separator (e.g. ' ' or 'T')
    (\d{2})           # 2-digit HOUR (e.g. '10')
    \D?               # optional 1 character non-digit separator (e.g. ' ' or ':')
    (\d{2})           # 2-digit MINUTE (e.g. '10')
    \D?               # optional 1 character non-digit separator (e.g. ' ' or ':')
    (\d{2})           # 2-digit SECOND (e.g. '10')
    """

    case2_regex = r"""
    # case 2: YYYYMMDDhhmm (no seconds) 
    (\d{4})     # 2- or 4-digit YEAR 
    \D?               # optional 1 character non-digit separator (e.g. ' ' or '-')
    (\d{2})           # 2-digit MONTH 
    \D?               # optional 1 character non-digit separator
    (\d{2})           # 2-digit DAY 
    \D?               # optional 1 character non-digit separator (e.g. ' ' or 'T')
    (\d{2})           # 2-digit HOUR 
    \D?               # optional 1 character non-digit separator (e.g. ' ' or ':')
    (\d{2})           # 2-digit MINUTE 
    """

    case3_regex = r"""
    # case 3: YYYYMMDDhh (no seconds, no minutes)
    (\d{4})     # 2- or 4-digit YEAR 
    \D?               # optional 1 character non-digit separator (e.g. ' ' or '-')
    (\d{2})           # 2-digit MONTH 
    \D?               # optional 1 character non-digit separator
    (\d{2})           # 2-digit DAY 
    \D?               # optional 1 character non-digit separator (e.g. ' ' or 'T')
    (\d{2})           # 2-digit HOUR 
    """

    case4_regex = r"""
    # case 4: YYYYMMDD (no time values, just date)
    (\d{4})     # 2- or 4-digit YEAR 
    \D?               # optional 1 character non-digit separator (e.g. ' ' or '-')
    (\d{2})           # 2-digit MONTH 
    \D?               # optional 1 character non-digit separator
    (\d{2})           # 2-digit DAY 
    """

    case5_regex = r"""
    # case 5: YYYYMM (no time values, just month year)
    (\d{4})     # 2- or 4-digit YEAR 
    \D?               # optional 1 character non-digit separator (e.g. ' ' or '-')
    (\d{2})           # 2-digit MONTH 
    """

    case6_regex = r"""
    # case 6: YYMMDDhhmmss 
    (\d{2})     # 2- or 4-digit YEAR (e.g. '07' or '2007')
    \D?               # optional 1 character non-digit separator (e.g. ' ' or '-')
    (\d{2})           # 2-digit MONTH (e.g. '12')
    \D?               # optional 1 character non-digit separator
    (\d{2})           # 2-digit DAY of month (e.g. '10')
    \D?               # optional 1 character non-digit separator (e.g. ' ' or 'T')
    (\d{2})           # 2-digit HOUR (e.g. '10')
    \D?               # optional 1 character non-digit separator (e.g. ' ' or ':')
    (\d{2})           # 2-digit MINUTE (e.g. '10')
    \D?               # optional 1 character non-digit separator (e.g. ' ' or ':')
    (\d{2})           # 2-digit SECOND (e.g. '10')
    """

    case7_regex = r"""
    # case 7: YYMMDDhhmm (no seconds) 
    (\d{2})     # 2- or 4-digit YEAR 
    \D?               # optional 1 character non-digit separator (e.g. ' ' or '-')
    (\d{2})           # 2-digit MONTH 
    \D?               # optional 1 character non-digit separator
    (\d{2})           # 2-digit DAY 
    \D?               # optional 1 character non-digit separator (e.g. ' ' or 'T')
    (\d{2})           # 2-digit HOUR 
    \D?               # optional 1 character non-digit separator (e.g. ' ' or ':')
    (\d{2})           # 2-digit MINUTE 
    """

    case8_regex = r"""
    # case 8: YYMMDDhh (no seconds, no minutes)
    (\d{2})     # 2- or 4-digit YEAR 
    \D?               # optional 1 character non-digit separator (e.g. ' ' or '-')
    (\d{2})           # 2-digit MONTH 
    \D?               # optional 1 character non-digit separator
    (\d{2})           # 2-digit DAY 
    \D?               # optional 1 character non-digit separator (e.g. ' ' or 'T')
    (\d{2})           # 2-digit HOUR 
    """

    case9_regex = r"""
    # case 9: YYMMDD (no time values, just date)
    (\d{2})     # 2- or 4-digit YEAR 
    \D?               # optional 1 character non-digit separator (e.g. ' ' or '-')
    (\d{2})           # 2-digit MONTH 
    \D?               # optional 1 character non-digit separator
    (\d{2})           # 2-digit DAY 
    """

    case10_regex = r"""
    # case 10: YYMM (no time values, just month year)
    (\d{2})     # 2- or 4-digit YEAR 
    \D?               # optional 1 character non-digit separator (e.g. ' ' or '-')
    (\d{2})           # 2-digit MONTH 
    """

    ##  Verbose regular expressions require use of re.VERBOSE flag.
    ##  so we can use multiline regexp

    # cases are ordered from precise to more coarse resolution of time
    cases = [case1_regex, case2_regex, case3_regex, case4_regex, case5_regex, case6_regex, case7_regex, case8_regex, case9_regex]
    patterns = [re.compile(c, re.VERBOSE) for c in cases]
    matches = [p.search(input_string) for p in patterns]

    # for testing, try to computer datetime objects
    # just because there is a match does not mean it makes sense
    for ind in range(len(matches)):
        if bool(matches[ind]):
            # print matches[ind].groups()
            bits = matches[ind].groups()
            values = [int(yi) for yi in bits]
            # check for 2-digit year 
            if values[0] < 50:
                values[0] += 2000
            elif values[0]>=50 and values[0]<100:
                values[0] += 1900
            #
            # we must have at least 3 arg input to datetime
            if len(values)==1:
                values.extend([1,1]) # add First of January
            elif len(values)==2:
                values.extend([1]) # add first day of month

            #
            # compute dt
            try:
                dt = datetime(*values)
            except ValueError, e:
                # value error if something not valid for datetime
                # e.g. month 1...12, something parsed wrong
                dt = None
            else:
                # absolute difference in days from now (UTC)
                z = dt - datetime.utcnow()
                daysdiff = abs(z.days)
                # if this date unreasonable (>10 years*365), throw it out
                # garbage was parsed
                if daysdiff > 3600:
                    dt = None                
        else:
            dt = None
        # place datetime object or None within sequence of matches
        matches[ind] = dt

    # find the first (most precise) date match since there might be more than
    # as we searched more coarse templates, but now we have thrown out 
    
    b = [bool(x) for x in matches]
    try:
        ind = b.index(True)
    except ValueError, e:
        print 'filt_datetime: No date found in ', input_string
        dt = None
    else:
       dt = matches[ind]
       if gran:
           return dt,ind
       else:
           return dt

def display_time_diff(diff):
    """Display time difference in HH:MM:DD using number weeks (W)
    and days (D) if necessary"""
    # weeks, days = divmod(diff.days, 7)
    days = diff.days
    minutes, seconds = divmod(diff.seconds, 60)
    hours, minutes = divmod(minutes, 60)    
    # if (weeks>2 and days>0):
    #    str = "%d Weeks, %d Days %02d:%02d" % (days, hours, minutes)
    if (days==1):
        str = "%02d:%02d" % (24+hours, minutes)
    elif (days>1):
        str = "%d Days %02d:%02d" % (days, hours, minutes)
    else:
        str = "%02d:%02d" % (hours, minutes)
    return str

def copy_loop_sequence(src, dst, fn_glob, numFiles=24):
    """ """
    # src = '/seacoos/data/nccoos/level3/bogue/adcpwaves/dspec/'+this_month.strftime("%Y_%m")
    # dst = '/home/haines/rayleigh/loop/'
    # fn_glob = 'bogue_dspec_plot*'

def addnan(dt, data, maxdelta=None):
    """
    insert NaN for time gaps

    :Parameters:
        dt : numpy.array of datetime
        data : numpy.array of data
        maxdelta : size of time gap (fraction or number of days) to insert
            [default is two times its own sample interval]

    :Returns: 
        new_dt : numpy.array of datetime
        new_data : numpy.array of data


    """ 
    # dt to be only 1-dimension and data to be 1- or 2-dimensional
    
    from matplotlib.dates import date2num, num2date

    # print dt.shape
    # print data.shape
    
    dn = date2num(dt)
    delta = numpy.diff(dn)
    sample_interval = numpy.median(delta)
    if maxdelta==None:
        maxdelta = 2.*sample_interval
    # print maxdelta
    igap = (delta > maxdelta).nonzero()[0]
    ngap = len(igap)
    if not ngap:
        return (dt, data)
    else:
        # convert sample interval to dt object
        sample_interval = timedelta(0.5*sample_interval)
        # for each gap in time create datetime value
        dt_insert = [dt[gap]+sample_interval for gap in igap]
        # insert new sample times at indices of the gaps
        new_dt = numpy.insert(numpy.array(dt), igap+1, dt_insert)
        # insert NaN value at the gaps (insert placed just before obs)
        new_data = numpy.insert(numpy.array(data, dtype=float), igap+1, numpy.nan, axis=0)
        # if all the data is NaN, then autoscale crocks.  This prevents
        # throwing an error (but be careful if using for anything other than grafs)
        if numpy.isnan(new_data).all():
            new_data[-1]=0.
        return (new_dt, new_data)

#

# unit conversion using udunits
def udconvert(val, units_from, units_to):
    """Convert units using NCAR UDUNITS-2

    Convert data to another unit using UDUNITS-2 API.

    :Parameters:
       val : scalar or list of scalars, numpy.array
         Data to be converted
       units_from : string
         Units from which the values to be converted
       units_to : string
         Units to which the values will be converted

    :Returns:
       val_to : float scalar, list, or numpy.array
         Data that is converted to new units
       units_to : string
         Units to which the data are now converted

    Files
    -----
    XML file that can be edited to change and add new conversions
    /usr/local/share/udunits/udunits-common.xml

    Not recommended to edit but useful info on UDUNITS-2 
    udunits2-accepted.xml
    udunits2-base.xml
    udunits2-derived.xml
    udunits2-prefixes.xml
    udunits2.xml
    
    """
    import udunits
    cnv = udunits.udunits(units_from, units_to)

    if cnv[0]==0:
        val_to = val*cnv[1] + cnv[2]
        # if val_to > 99:
        #     val_to_str = '%.4g (%s)' % (val_to, valunits_to)
        # else:
        #     val_to_str = '%.2g (%s)' % (val_to, valunits_to)
    else:
        print cnv
        return (None, None)

    # TO DO: Need to handle errors in a better fashion
    # [-1, 'Unable to parse from', 'NTU', -3, 'Conversion not possible']
    # [-2, 'Unable to parse to', 'NTU', -3, 'Conversion not possible']
    # [-3, 'Conversion not possible']
    return (val_to, units_to)

# the following to be deprecated by udunits2 API
def meters2feet(meters):
    """Convert meters to feet: <feet> = <meters>*3.28084 """
    return meters*3.28084
        
def feet2meters(feet):
    """Convert feet to meters: <meters> = <feet>*0.3048 """
    return feet*0.3048
        
def millibar2inches_Hg(millibar):
    """Convert millibars to inches Hg: <inches_Hg> = <millibar>*0.0295301 """
    return millibar*0.0295301

def celsius2fahrenheit(celsius):
    """Convert deg Celsius to deg Fahrenheit: <fahrenheit> = ((1.8*<celsius>)+32) """
    return (1.8*celsius)+32

def millimeters2inches(millimeters):
    """ Convert millimeter to inches: <inches> = <millimeters>*0.0393700787) """
    return millimeters*0.0393700787

def inches2millimeters(inches):
    """ Convert <mm> = <inches>*25.4 """
    return inches*25.4

def meters_sec2knots(meters_sec):
    """ Convert m/s to knots: <knots> = <meters_sec>*1.94384449) """
    return meters_sec*1.94384449

def wind_vector2u(wind_speed, wind_from_direction):
    """ Convert wind vector to U (east) component: <u> = <wind_speed>*sine(<wind_from_direction>*pi/180) """
    return wind_speed*math.sin(wind_from_direction*math.pi/180)

def wind_vector2v(wind_speed, wind_from_direction):
    """ Convert wind vector to V (north) component: <v> = <wind_speed>*cosine(<wind_from_direction>*pi/180) """
    return wind_speed*math.cos(wind_from_direction*math.pi/180)

def proc2latest(pi, si, yyyy_mm):
    """Select specific variables and times from current monthly netCDF
    and post as latest data.  TEST MODE.

    For each active config file, load specific variables from NCCOOS
    monthly netCDF, make any necessary changes to data or attributes
    conform to SEACOOS Data Model, subset data (last 48 hours), and
    create new netCDF file in latest netCDF directory.

    NOTE: In test mode right now. See auto() function for similar action.

    """
    
    platform = pi['id']
    package = si['id']
    # input file
    si['proc_filename'] = '%s_%s_%s.nc' % (platform, package, yyyy_mm)
    ifn = os.path.join(si['proc_dir'], si['proc_filename'])
    # output file
    si['latest_filename'] = 'nccoos-%s-%s-latest.nc' % (platform, package)
    ofn = os.path.join(si['latest_dir'], si['latest_filename'])
    if os.path.exists(ifn):
        print ' ... ... latest : %s ' % (ofn,)
        # get dt from current month file
        (es, units) = nc_get_time(ifn)
        dt = [es2dt(e) for e in es]
        last_dt = dt[-1]
    else:
        # no input then remove output if exists and exit
        print " ... ... latest: NO latest file created"
        if os.path.exists(ofn):
            os.remove(ofn)
        return

    # determine which index of data is within the specified timeframe (last 2 days)
    n = len(dt)
    idx = numpy.array([False for i in range(n)])
    for i, val in enumerate(dt):
        if val>last_dt-timedelta(days=2) and val<=last_dt+timedelta(seconds=360):
            idx[i] = True
    dt = numpy.array(dt)
    dt = dt[idx]

    # read in data and unpack tuple
    d = nc_load(ifn, si['latest_vars'])
    global_atts, var_atts, dim_inits, var_inits, var_data = d
    list_of_record_vars = nc_find_record_vars(ifn)

    # turn off unlimited dimension (SH NOTE: As of pycdf-0.6-3b cannot
    # delete a dimension or reset unlimited to limited within either
    # CDF or CDFDim class, so doing it manually here by setting list
    # 'dim_init' before creating of new netcdf.)
    dim_inits = list(dim_inits)
    for i in range(len(dim_inits)):
        if dim_inits[i][1]==0:
            dim_inits[i] = ('ntime', len(dt))        
    dim_inits = tuple(dim_inits)

    # subset data
    varNames = [vn for vn, vt, vd in var_inits]
    var_data = list(var_data)
    for i in range(len(varNames)):
        vn, vd = var_data[i]

        if vn in list_of_record_vars:
            var_data[i]=(vn, vd[idx])
    var_data = tuple(var_data)

    global_atts['start_date'] = dt[0].strftime('%Y-%m-%d %H:%M:%S')
    d = (global_atts, var_atts, dim_inits, var_inits, var_data)

    # write latest data
    nc_create(ofn, d)

    # quick way to rename dimensions 
    nc_rename_dimension(ofn, 'ntime', 'time')
    nc_rename_dimension(ofn, 'nlat', 'lat')
    nc_rename_dimension(ofn, 'nlon', 'lon')
    nc_rename_dimension(ofn, 'nz', 'z')

    # global replace _FillValue
    nc_replace_fillvalue(ofn, -99999.0)

def proc2csv(pi, si, yyyy_mm):
    """Select specific variables and times from current monthly netCDF
    and post file of csv data.  TEST MODE.

    For each active config file, load specific variables from NCCOOS
    monthly netCDF, make any necessary changes to data or attributes
    conform to CSV output, subset data, and
    create new file in csv directory.

    NOTE: See auto() function for similar action.

    """
    
    platform = pi['id']
    package = si['id']
    # input file
    si['proc_filename'] = '%s_%s_%s.nc' % (platform, package, yyyy_mm)
    ifn = os.path.join(si['proc_dir'], si['proc_filename'])
    # output file
    si['csv_filename'] = 'nccoos_%s_%s_latest.csv' % (platform, package)
    ofn = os.path.join(si['csv_dir'], si['csv_filename'])
    f = open(ofn, 'w')
    
    if os.path.exists(ifn):
        print ' ... ... csv : %s ' % (ofn,)
        # get dt from current month file
        (es, units) = nc_get_time(ifn)
        dt = [es2dt(e) for e in es]
        last_dt = dt[-1]
    else:
        # no input then report fact csv file 
        print ' ... ... csv: NO csv data reported '
        f.write('"No DATA REPORTED", " \\- ", " \\- "\n')
        f.close()
        return
    
    # determine which index of data is within the specified timeframe (last 2 days)
    n = len(dt)
    idx = numpy.array([False for i in range(n)])
    for i, val in enumerate(dt):
        if val>last_dt-timedelta(days=1) and val<=last_dt+timedelta(seconds=360):
            idx[i] = True
    dt = numpy.array(dt)
    dt = dt[idx]

    # read in data and unpack tuple
    d = nc_load(ifn, si['csv_vars'])
    global_atts, var_atts, dim_inits, var_inits, var_data = d

    # dts = es2dt(dt[-1])
    # set timezone info to UTC (since data from level1 should be in UTC!!)
    last_dt = last_dt.replace(tzinfo=tzutc())
    # return new datetime based on computer local
    last_dt_local = last_dt.astimezone(tzlocal())
    
    diff = abs(last_dt - last_dt_local)
    if diff.days>0:
        last_dt_str = last_dt.strftime("%H:%M %Z on %b %d, %Y") + \
                      ' (' + last_dt_local.strftime("%H:%M %Z, %b %d") + ')'
    else:
        last_dt_str = last_dt.strftime("%H:%M %Z") + \
                      ' (' + last_dt_local.strftime("%H:%M %Z") + ')' \
                      + last_dt.strftime(" on %b %d, %Y")

    # uses dateutil.tz.tzutc() from dateutil 
    now_utc_dt = datetime.now(tzutc())
    now_utc_dt = now_utc_dt.replace(second=0, microsecond=0)
    # uses dateutil.tz.tzlocal() from dateutil to get timezone settings as known by the operating system
    now_local_dt = datetime.now(tzlocal())
    now_local_dt = now_local_dt.replace(second=0, microsecond=0)
    # if more than a day difference between local time and UTC, specify dates for each
    # otherwise date for one is sufficient (cuts down on clutter)
    diff = abs(now_local_dt - now_utc_dt)
    if diff.days>0:
        now_str = now_utc_dt.strftime("%H:%M %Z on %b %d, %Y") + \
                  ' (' + now_local_dt.strftime("%H:%M %Z, %b %d") + ')'
    else:
        now_str = now_utc_dt.strftime("%H:%M %Z") + \
                  ' (' + now_local_dt.strftime("%H:%M %Z") + ')' \
                  + now_utc_dt.strftime(" on %b %d, %Y")

    # how old is the data
    stale_diff = abs(now_utc_dt - last_dt)
    if stale_diff.days>0 or stale_diff.seconds>=8*60*60:
        stale_str = display_time_diff(stale_diff)
    else:
        stale_str = '' # use empty string to keep background white
            
    varNames = [vn for vn, vt, vd in var_inits]
    var_data = list(var_data)
    for i in range(len(varNames)):
        vn, vd = var_data[i]
        vd = vd[idx]

        # (1) var name and units (first td)
        var_name_str = '%s (%s)' % (var_atts[vn]['long_name'], var_atts[vn]['short_name'])
        valunits = var_atts[vn]['units']
        if vn=='rain':
            val = vd.sum()
            var_name_str = 'Rain Total (24 hrs)'
        else:
            val = vd[-1]

        # if can take the length of val, val is probably a list, tuple of profile data
        # there will be more than one value of which we want a mean (ignoring NaN')
        if bool('__len__' in dir(val)):
            val = numpy.mean(numpy.ma.masked_where(numpy.isnan(val), val))
            var_name_str = 'Depth Averaged '+var_name_str

        # to metric
        import udunits

        sn = var_atts[vn]['standard_name']
        valunits_from = valunits
        if 'temperature' in sn or sn in ('wind_chill', 'dew_point'):            
            if valunits_from == 'degrees Celsius':
                valunits_from = 'degC'
            valunits_to = 'degC'
        elif 'velocity' in sn or 'speed' in sn or 'current' in sn:
            valunits_to = 'm s-1'
        elif 'flux' in sn or sn in ('discharge',):
            if valunits_from == 'cfs':
                valunits_from = 'ft^3/sec'
            valunits_to = 'm^3/s'
        elif 'rain' in sn:
            valunits_to = 'mm'
        elif 'level' in sn or 'height' in sn or 'depth' in sn:
            valunits_to = 'm'
        else:
            # can't find a conversion we want so convert to itself
            valunits_to = valunits_from
            
        cnv = udunits.udunits(valunits_from, valunits_to)

        if cnv[0]==0:
            val_to = val*cnv[1] + cnv[2]
            if val_to > 99:
                metric_str = '%.4g (%s)' % (val_to, valunits_to)
            else:
                metric_str = '%.2g (%s)' % (val_to, valunits_to)
        # handle errors
        # [-1, 'Unable to parse from', 'NTU', -3, 'Conversion not possible']
        # [-2, 'Unable to parse to', 'NTU', -3, 'Conversion not possible']
        # [-3, 'Conversion not possible']
        elif cnv[0]==-1 or cnv[0]==-2:
            if val > 99:
                metric_str = '%.4g (%s)' % (val, valunits)
            else:
                metric_str = '%.2g (%s)' % (val, valunits)
        else:
            metric_str = '\-'
                
        # to english units
        if 'temperature' in sn or sn in ('wind_chill', 'dew_point'):            
            if valunits_from == 'degrees Celsius':
                valunits_from = 'degC'
            valunits_to = 'degF'
        elif 'velocity' in sn or 'speed' in sn or 'current' in sn:
            valunits_to = 'knots'
        elif 'flux' in sn or sn in ('discharge',):
            if valunits_from == 'cfs':
                valunits_from = 'ft^3/sec'
            valunits_to = 'ft^3/s'
        elif 'rain' in sn:
            valunits_to = 'in'
        elif 'level' in sn or 'height' in sn or 'depth' in sn:
            valunits_to = 'ft'
        else:
            valunits_to = valunits_from
        # 
        cnv = udunits.udunits(valunits_from, valunits_to)
        if cnv[0]==0:
            val_to = val*cnv[1] + cnv[2]            
            if val > 99:
                english_str ='%.4g (%s)' % (val_to, valunits_to)
            else:
                english_str = '%.2g (%s)' % (val_to, valunits_to)
        # handle errors
        # [-1, 'Unable to parse from', 'NTU', -3, 'Conversion not possible']
        # [-2, 'Unable to parse to', 'NTU', -3, 'Conversion not possible']
        # [-3, 'Conversion not possible']
        elif cnv[0]==-1 or cnv[0]==-2:
            if val > 99:
                english_str = '%.4g (%s)' % (val, valunits)
            else:
                english_str = '%.2g (%s)' % (val, valunits)
        else:
            english_str = '\-'

        if metric_str == english_str:
            english_str = '\-'
       
        if vn=='time':
            f.write('"**%s:** %s", ""\n' % ('Sample Time', last_dt_str))
        elif vn=='blank':
             f.write('"%s", "%s", "%s"\n' % (' ', ' ', ' '))
        else:
            f.write('"%s", "%s", "%s"\n' % (var_name_str, metric_str, english_str))

    f.close()




