#!/usr/bin/env python
# Last modified:  Time-stamp: <2012-04-27 09:09:11 haines>
"""Process raw data to monthly netCDF data files

This module processes raw ascii- or binary-data from different NCCOOS
sensors (ctd, adcp, waves-adcp, met) based on manual or automated
operation.  If automated processing, add raw data (level0) from all
active sensors to current month's netcdf data files (level1) with the
current configuration setting.  If manual processing, determine which
configurations to use for requested platform, sensor, and month.

:Processing steps:
  0. raw2proc auto or manual for platform, sensor, month
  1. list of files to process 
  2. parse data
  3. create, update netcdf

  to-do
  3. qc (measured) data 
  4. process derived data (and regrid?) 
  5. qc (measured and derived) data flags

"""

__version__ = "v0.1"
__author__ = "Sara Haines <sara_haines@unc.edu>"

import sys
import os
import re
import traceback

# for production use:
# defconfigs='/home/haines/nccoos/raw2proc'
# for testing use:
# defconfigs='/home/haines/nccoos/test/r2p'

# define config file location to run under cron
defconfigs='/opt/env/haines/dataproc/raw2proc'

import numpy

from procutil import *
from ncutil import *

REAL_RE_STR = '\\s*(-?\\d(\\.\\d+|)[Ee][+\\-]\\d\\d?|-?(\\d+\\.\\d*|\\d*\\.\\d+)|-?\\d+)\\s*'
NAN_RE_STR = '[Nn][Aa][Nn]'

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

def import_parser(name):
    mod = __import__('parsers')
    parser = getattr(mod, name)
    return parser

def import_processors(mod_name):
    mod = __import__(mod_name)
    parser = getattr(mod, 'parser')
    creator = getattr(mod, 'creator')
    updater = getattr(mod, 'updater')
    return (parser, creator, updater)
    

def get_config(name):
    """Usage Example >>>sensor_info = get_config('bogue_config_20060918.sensor_info')"""
    components = name.split('.')
    mod = __import__(components[0])
    for comp in components[1:]:
        attr = getattr(mod, comp)
    return attr

def get_config_dates(pi):
    """ Get datetime of both start and end setting within config file

    Example
    -------
        >>> pi = get_config(cn+'.platform_info')
        >>> (config_start_dt, config_end_dt) = get_config_dates(pi)

    """
    now_dt = datetime.utcnow()
    now_dt.replace(microsecond=0)
    if pi['config_start_date']:
        config_start_dt = filt_datetime(pi['config_start_date'])
    elif pi['config_start_date'] == None:
        config_start_dt = now_dt
    if pi['config_end_date']:
        config_end_dt = filt_datetime(pi['config_end_date'])
    elif pi['config_end_date'] == None:
        config_end_dt = now_dt
    return (config_start_dt, config_end_dt)

def find_configs(platform, yyyy_mm, config_dir=''):
    """Find which configuration files for specified platform and month

    :Parameters:
       platform : string
           Platfrom id to process (e.g. 'bogue')
       yyyy_mm : string
           Year and month of data to process (e.g. '2007_07')

    :Returns:
       cns : list of str
           List of configurations that overlap with desired month
           If empty [], no configs were found
    """
    import glob
    # list of config files based on platform
    configs = glob.glob(os.path.join(config_dir, platform + '_config_*.py'))
    configs.sort()
    # determine when month starts and ends
    (prev_month, this_month, next_month) = find_months(yyyy_mm)
    month_start_dt = this_month
    month_end_dt = next_month - timedelta(seconds=1)
    # print month_start_dt; print month_end_dt
    # 
    cns = []
    for config in configs:
        cn = os.path.splitext(os.path.basename(config))[0]
        pi = get_config(cn+'.platform_info')
        (config_start_dt, config_end_dt) = get_config_dates(pi)
        if (config_start_dt <= month_start_dt or config_start_dt <= month_end_dt) and \
               (config_end_dt >= month_start_dt or config_end_dt >= month_end_dt):
            cns.append(cn)
    return cns


def find_active_configs(config_dir=defconfigs):
    """Find which configuration files are active

    :Returns:
       cns : list of str
           List of configurations that overlap with desired month
           If empty [], no configs were found
    """
    import glob
    # list of all config files 
    configs = glob.glob(os.path.join(config_dir, '*_config_*.py'))
    cns = []
    for config in configs:
        # datetime from filename 
        cn = os.path.splitext(os.path.basename(config))[0]
        pi = get_config(cn+'.platform_info')
        if pi['config_end_date'] == None:
            cns.append(cn)
    return cns


def uniqify(seq):
    seen = {}
    result = []
    for item in seq:
        # in old Python versions:
        # if seen.has_key(item)
        # but in new ones:
        if item in seen: continue
        seen[item] = 1
        result.append(item)
    return result
                                                       

def get_all_platforms(config_dir=defconfigs):
    """Get all platform ids

    :Returns:
       pids : list of str
           Sorted list of all the platforms
    """
    import glob
    # list of all config files 
    configs = glob.glob(os.path.join(config_dir, '*_config_*.py'))
    configs.sort()
    pids = []
    for config in configs:
        # datetime from filename 
        cn = os.path.splitext(os.path.basename(config))[0]
        pi = get_config(cn+'.platform_info')
        if pi['id']:
            pids.append(pi['id'])
    pids = uniqify(pids)
    pids.sort()
    return pids

def get_all_packages(platform, config_dir=defconfigs):
    """Get all package ids -- all defined packages in sensor_info{} from all configs for the platform

    :Returns:
       sids : list of str
           Sorted list of all the sensor ids for package
    """
    import glob
    # list of all config files 
    configs = glob.glob(os.path.join(config_dir, platform + '_config_*.py'))
    configs.sort()
    #
    sids = []
    for config in configs:
        cn = os.path.splitext(os.path.basename(config))[0]
        pi = get_config(cn+'.platform_info')
        sids.extend(list(pi['packages']))
    sids = uniqify(sids)
    sids.sort()
    return sids

def get_all_platform_configs(platform, config_dir=defconfigs):
    """Get all the config files for a platform

    :Returns:
       cns : list of config names
           Sorted list of all the sensor ids for package
    """
    import glob
    # list of all config files 
    configs = glob.glob(os.path.join(config_dir, platform + '_config_*.py'))
    configs.sort()
    #
    cns = []
    for config in configs:
        cn = os.path.splitext(os.path.basename(config))[0]
        cns.append(cn)
    return cns

def get_config_packages(cn):
    """ Get active packages set in platform_info{} from specific config file

    :Returns:
       sids : list of str
           Sorted (default) or unsorted list of all the sensor ids for package
           If empty [], no platform ids were found
    """
    pi = get_config(cn+'.platform_info')
    sids = list(pi['packages'])
    return sids

def list_months(dts, dte):
    """ list of datetimes for all months inclusively within given date range 
    
    """
    lom = []
    if type(dts) == type(dte) == type(datetime.utcnow()) and dts <= dte:
        years = range(dts.year,dte.year+1)
        for yyyy in years:
            if yyyy > dts.year:
                a = 1
            else:
                a = dts.month
            if yyyy < dte.year:
                b = 12
            else:
                b = dte.month
            months = range(a, b+1)
            for mm in months:
                lom.append(datetime(yyyy, mm, 1).strftime('%Y_%m'))
    else:
        print "list_months requires two inputs type datetime.datetime and dts<dte"
    return lom
    

def create_spin_list(plats, packs, dates, config_dir=defconfigs):
    """ create list of params needed to run manual() mutiple ways

    :Returns:
       spin_list : list of three-tuple each tuple with form (platform, package, yyyy_mm)

    Notes
    -----

    1. plats -- 'ALL' or ['b1', 'b2']
    2. packs -- 'ALL' or ['ctd1', 'ctd2']
    3. dates -- 'ALL' or ['2011_11', '2011_12'] or [dt.datetime(2006,1,1), dt.nowutc()]

    For each platform determin packages for given dates
    also a good way to get listing platforms and packages for specified dates

    """
    result = []
    platforms = []
    if type(plats) == str:
        if plats.upper() == 'ALL':
            platforms = get_all_platforms()
        else:
            platforms = [plats] # make one platform iterable
        
    print ' Expanded lists for creating spin_list:'
    print ' ...  platform ids : %s' % platforms

    for platform in platforms:
        if len(platforms)>1:
            print '------------------------------------'
            print ' ... ... platform : %s ' % platform
        packages = []
        if type(packs) == str:
            if packs.upper() == 'ALL':
                packages = get_all_packages(platform)
            else:
                packages = [packs] # make one package iterable

        print ' ... ... packages : %s' % packages
        for package in packages:
            # dates is a string 'ALL' or format 'YYYY_MM'
            months = []
            if type(dates) == str:
                if dates.upper() == 'ALL':
                    cns = get_all_platform_configs(platform)
                    months = []
                    for cn in cns:
                        pi = get_config(cn+'.platform_info')
                        (dts, dte) = get_config_dates(pi)
                        if package in pi['packages']:
                            months.extend(list_months(dts, dte))
                else:
                    months = [dates] # make on date iterable
            # dates is a list
            if type(dates) == type([]):
                # if dates has two datetime types
                if type(dates[0]) == type(dates[1]) == type(datetime.utcnow()):
                    dt1, dt2 = dates
                    cns = get_all_platform_configs(platform)
                    months = []
                    for cn in cns:
                        pi = get_config(cn+'.platform_info')
                        (dts, dte) = get_config_dates(pi)

                        if dts<=dt1 and dt1<=dte: a = dt1
                        elif dt1<=dts and dt1<=dte: a = dts

                        if dts<dt2 and dt2<=dte: b = dt2
                        elif dts<dt2 and dte<=dt2: b = dte

                        if dte<dt1 or dt2<dts:
                            continue
                        # list only months that are in configs for wide date range
                        if package in pi['packages']:
                            months.extend(list_months(a,b))
                # else if string in list
                elif type(dates[0]) == str:
                    months = dates
            print ' ... ...   months : %s' % months
            for month in months:
                # print '... ... %s %s %s' % (platform, package, month)
                result.append((platform, package, month))
                
    return result
                
def find_raw(si, yyyy_mm):
    """Determine which list of raw files to process for month """
    import glob

    months = find_months(yyyy_mm)
    # list all the raw files in prev-month, this-month, and next-month
    all_raw_files = []
    m = re.search('\d{4}_\d{2}$', si['raw_dir'])
    if m:
        # look for raw_file_glob in specific directory ending in YYYY_MM
        # but look no further.  
        gs = os.path.join(si['raw_dir'], si['raw_file_glob'])
        all_raw_files.extend(glob.glob(gs))
    else:
        # no YYYY_MM at end of raw_dir then look for files
        # in prev-month, this-month, and next-month
        for mon in months:
            mstr = mon.strftime('%Y_%m')
            gs = os.path.join(si['raw_dir'], mstr, si['raw_file_glob'])
            all_raw_files.extend(glob.glob(gs))
            
    all_raw_files.sort()
        
    # 
    dt_start = si['proc_start_dt']-timedelta(days=1)
    dt_end = si['proc_end_dt']+timedelta(days=1)
    raw_files = []; raw_dts = []
    # compute datetime for each file
    for fn in all_raw_files:
        (fndt, granularity) = filt_datetime(os.path.basename(fn), gran=True)
        if granularity == 4:
	    # change dt_start to before monthly filename filt_datetime() date
            # for filenames with just YYYY_MM or YYYYMM add or substract 30 days to
            # see if it falls within config range.  It won't hurt to add names to files
            # parsed.
	    dt_start = si['proc_start_dt']-timedelta(days=31)
            # print dt_start
        if fndt:
            if dt_start <= fndt <= dt_end or m:
                raw_files.append(fn)
                raw_dts.append(fndt) 
    return (raw_files, raw_dts)

def which_raw(pi, raw_files, dts):
    """Further limit file names based on configuration file timeframe """
    (config_start_dt, config_end_dt) = get_config_dates(pi)

    for idx, fn in enumerate(raw_files):
        (fndt, granularity) = filt_datetime(os.path.basename(fn), gran=True)
        if granularity == 4:
            if fndt < config_start_dt:
                dts[idx] = config_start_dt 
            if fndt > config_end_dt:
                dts[idx] = config_end_dt

    new_list = [raw_files[i] for i in range(len(raw_files)) \
                     if config_start_dt <= dts[i] <= config_end_dt]

    if not new_list:
        new_list = [raw_files[i] for i in range(len(raw_files)) \
                    if dts[i] <= config_end_dt]
        
    return new_list
        

def raw2proc(proctype, platform=None, package=None, yyyy_mm=None):
    """
    Process data either in auto-mode or manual-mode

    If auto-mode, process newest data for all platforms, all
    sensors. Otherwise in manual-mode, process data for specified
    platform, sensor package, and month.

    :Parameters:
       proctype : string
           'auto' or 'manual' or 'spin'

       platform : string
           Platfrom id to process (e.g. 'bogue')
       package : string
           Sensor package id to process (e.g. 'adcp')
       yyyy_mm : string
           Year and month of data to process (e.g. '2007_07')

    Examples
    --------
    >>> raw2proc(proctype='manual', platform='bogue', package='adcp', yyyy_mm='2007_06')
    >>> raw2proc('manual', 'bogue', 'adcp', '2007_06')

    Spin
    ----
    platform can be list of platforms or 'ALL'
    package can be list packages or 'ALL'
    yyyy_mm can be list of months, or datetime range
    
    >>> raw2proc('spin', ['b1','b2'], ['ctd1', 'ctd2'], ['2011_11'])
    >>> raw2proc('spin', ['b1','b2'], ['ctd1', 'ctd2'], 'ALL')
    >>> raw2proc('spin', ['b1','b2'], ['ctd1', 'ctd2'], [datetime(2011,11,1), datetime(2012,4,1)])
    >>> raw2proc('spin', ['b1','b2'], 'ALL', 'ALL')
    
    Not a good idea but this will reprocess all the data from level0 
    >>> raw2proc('spin', 'ALL', 'ALL', 'ALL')
          
    """
    print '\nStart time for raw2proc: %s\n' % start_dt.strftime("%Y-%b-%d %H:%M:%S UTC")

    if proctype == 'auto':
        print 'Processing in auto-mode, all platforms, all packages, latest data'
        auto()
    elif proctype == 'manual':
        if platform and package and yyyy_mm:
            print 'Processing in manual-mode ...'
            print ' ...  platform id : %s' % platform
            print ' ... package name : %s' % package
            print ' ...        month : %s' % yyyy_mm
            print ' ...  starting at : %s' % start_dt.strftime("%Y-%m-%d %H:%M:%S UTC")
            manual(platform, package, yyyy_mm)
        else:
            print 'raw2proc: Manual operation requires platform, package, and month'
            print "   >>> raw2proc(proctype='manual', platform='bogue', package='adcp', yyyy_mm='2007_07')"
    elif proctype == 'spin':
        if platform and package and yyyy_mm:
            print 'Processing in spin-mode ...'
            print ' ...  platform ids : %s' % platform
            print ' ... package names : %s' % package
            print ' ...        months : %s' % yyyy_mm
            print ' ...   starting at : %s' % start_dt.strftime("%Y-%m-%d %H:%M:%S UTC")
            spin_list = create_spin_list(platform, package, yyyy_mm)
            spin(spin_list)
        else:
            print "raw2proc: Spin operation requires platform(s), package(s), and month(s)"
            print "   >>> raw2proc(proctype='spin', platform='b1', package='ALL', yyyy_mm='ALL')"
            print "   >>> raw2proc(proctype='spin', platform='ALL', package='met', yyyy_mm='2011_11')"
            print "   >>> raw2proc('spin', ['b1','b2'], ['ctd1', 'ctd2'], [datetime(2011,11,1), datetime(2012,4,1)])"

    else:
        print 'raw2proc: requires either auto or manual operation'


def auto():
    """Process all platforms, all packages, latest data

    Notes
    -----
    
    1. determine which platforms (all platforms with currently active
       config files i.e. config_end_date is None
    2. for each platform
         get latest config
         for each package
           (determine process for 'latest' data) copy to new area when grabbed
           parse recent data
           yyyy_mm is the current month
           load this months netcdf, if new month, create this months netcdf
           update modified date and append new data in netcdf
           
    """
    yyyy_mm = this_month()
    months = find_months(yyyy_mm)
    month_start_dt = months[1]
    month_end_dt = months[2] - timedelta(seconds=1)

    configs = find_active_configs(config_dir=defconfigs)
    if configs:
        # for each configuration 
        for cn in configs:
            print ' ... config file : %s' % cn
            pi = get_config(cn+'.platform_info')
            asi = get_config(cn+'.sensor_info')
            platform = pi['id']
            (pi['config_start_dt'], pi['config_end_dt']) = get_config_dates(pi)

            # for each sensor package
            for package in asi.keys():
                try: # if package files, try next package
                    print ' ... package name : %s' % package
                    si = asi[package]
                    si['proc_filename'] = '%s_%s_%s.nc' % (platform, package, yyyy_mm)
                    ofn = os.path.join(si['proc_dir'], si['proc_filename'])
                    si['proc_start_dt'] = month_start_dt
                    si['proc_end_dt'] = month_end_dt
                    if os.path.exists(ofn):
                        # get last dt from current month file
                        (es, units) = nc_get_time(ofn)
                        last_dt = es2dt(es[-1])
                        # if older than month_start_dt use it instead to only process newest data
                        if last_dt>=month_start_dt:
                            si['proc_start_dt'] = last_dt

                    (raw_files, raw_dts) = find_raw(si, yyyy_mm)
                    raw_files = which_raw(pi, raw_files, raw_dts)
                    if raw_files:
                        process(pi, si, raw_files, yyyy_mm)
                    else:
                        print ' ... ... NOTE: no new raw files found'

                    # update latest data for SECOORA commons
                    if 'latest_dir' in si.keys():
                        # print ' ... ... latest : %s ' % si['latest_dir']
                        proc2latest(pi, si, yyyy_mm)

                    if 'csv_dir' in si.keys():
                        proc2csv(pi, si, yyyy_mm)
                except:
                    traceback.print_exc()
    #
    else:
        print ' ... ... NOTE: No active platforms'

def spin(spin_list):
    """ wrapper to run manual() for multiple months"""
    for item in spin_list:
        platform, package, yyyy_mm = item
        raw2proc('manual',platform, package, yyyy_mm)

def manual(platform, package, yyyy_mm):
    """Process data for specified platform, sensor package, and month

    Notes
    -----
    
    1. determine which configs
    2. for each config for specific platform
           if have package in config
               which raw files
    """
    months = find_months(yyyy_mm)
    month_start_dt = months[1]
    month_end_dt = months[2] - timedelta(seconds=1)
   
    configs = find_configs(platform, yyyy_mm, config_dir=defconfigs)

    if configs:
        # for each configuration 
        for index in range(len(configs)):
            cn = configs[index]
            print ' ... config file : %s' % cn
            pi = get_config(cn+'.platform_info')
            (pi['config_start_dt'], pi['config_end_dt']) = get_config_dates(pi)
            # month start and end dt to pi info
            asi = get_config(cn+'.sensor_info')
            if package in pi['packages']:
                si = asi[package]
                if si['utc_offset']:
                    print ' ... ... utc_offset : %g (hours)' % si['utc_offset']
                si['proc_start_dt'] = month_start_dt
                si['proc_end_dt'] = month_end_dt
                si['proc_filename'] = '%s_%s_%s.nc' % (platform, package, yyyy_mm)
                ofn = os.path.join(si['proc_dir'], si['proc_filename'])
                (raw_files, raw_dts) = find_raw(si, yyyy_mm)
                # print raw_files
                # print raw_dts
                raw_files = which_raw(pi, raw_files, raw_dts)
                # print raw_files
                # print raw_dts
                # remove any previous netcdf file (platform_package_yyyy_mm.nc)
                if index==0  and os.path.exists(ofn):
                    os.remove(ofn)
                # this added just in case data repeated in data files
                if os.path.exists(ofn):
                    # get last dt from current month file
                    (es, units) = nc_get_time(ofn)
                    last_dt = es2dt(es[-1])
                    # if older than month_start_dt use it instead to only process newest data
                    if last_dt>=month_start_dt:
                        si['proc_start_dt'] = last_dt

                if raw_files:
                    process(pi, si, raw_files, yyyy_mm)
                else:
                    print ' ... ... NOTE: no raw files found for %s %s for %s' % (package, platform, yyyy_mm)
                
            else:
                print ' ... ... NOTE: %s not operational on %s for %s' % (package, platform, yyyy_mm)                
    else:
        print ' ... ... ... NOTE: %s not operational for %s' % (platform, yyyy_mm)
    

def process(pi, si, raw_files, yyyy_mm):
    # tailored data processing for different input file formats and control over output
    (parse, create, update) = import_processors(si['process_module'])
    for fn in raw_files:
        # sys.stdout.write('... %s ... ' % fn)
        # attach file name to sensor info so parser can use it, if needed
        si['fn'] = fn
        lines = load_data(fn)
        if lines:
            data = parse(pi, si, lines)
            # determine which index of data is within the specified timeframe (usually the month)
            n = len(data['dt'])
            data['in'] = numpy.array([False for i in range(n)])

            for index, val in enumerate(data['dt']):
                if val>=pi['config_start_dt'] and \
                       val>=si['proc_start_dt'] and \
                       val<=si['proc_end_dt'] and \
                       val<=pi['config_end_dt']:
                    data['in'][index] = True
                    
            # if any records are in the month then write to netcdf
            if data['in'].any():
                sys.stdout.write(' ... %s ... ' % fn)
                sys.stdout.write('%d\n' % len(data['in'].nonzero()[0]))
                ofn = os.path.join(si['proc_dir'], si['proc_filename'])
                # update or create netcdf 
                if os.path.exists(ofn):
                    ut = update(pi,si,data)
                    nc_update(ofn, ut)
                else:
                    ct = create(pi,si,data)
                    nc_create(ofn, ct)
        else:
            # if no lines, file was empty
            print " ... skipping file %s" % (fn,)

    
# globals
start_dt = datetime.utcnow()
start_dt.replace(microsecond=0)

if __name__ == "__main__":
    import optparse
    raw2proc('auto')

    # for testing 
    # proctype='manual'; platform='bogue'; package='adcp'; yyyy_mm='2007_07'
    # raw2proc(proctype='manual', platform='bogue', package='adcp', yyyy_mm='2007_07')
