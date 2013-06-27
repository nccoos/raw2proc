#!/usr/bin/env python
# Last modified:  Time-stamp: <2010-12-09 16:14:39 haines>
"""
how to parse data, and assert what data and info goes into
creating and updating monthly netcdf files

parse data water level and flow data (pressure sensor only) collected
on Campbell Scientific DataLogger (loggernet) (csi)

parser : sample date and time, water_depth and flow from sontek and pressure

creator : lat, lon, z, time, rain, press_wl, press_flow
updator : time, rain, press_wl, press_flow


Examples
--------

>> (parse, create, update) = load_processors('proc_csi_adcp_v2')
or
>> si = get_config(cn+'.sensor_info')
>> (parse, create, update) = load_processors(si['adcp']['proc_module'])

>> lines = load_data(filename)
>> data = parse(platform_info, sensor_info, lines)
>> create(platform_info, sensor_info, data) or
>> update(platform_info, sensor_info, data)

"""


from raw2proc import *
from procutil import *
from ncutil import *

now_dt = datetime.utcnow()
now_dt.replace(microsecond=0)

def parser(platform_info, sensor_info, lines):
    """
    From FSL (CSI datalogger program files):
    
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
    10 TURB L
    11 PrDepthft  L
    12 Rain  L
    13 PrFlowcfs  L
    14 BattVolts  L

    Example data:
    
    1,2001,130,2000,19.27,.292,.1,.01,7.44,3.5,.123,0,12.77,0
    1,2001,130,2100,19.17,.291,.1,.01,7.38,3.1,.119,0,12.58,0
    1,2001,130,2200,19.06,.288,.1,.01,7.35,3.2,.12,0,12.72,0
    1,2001,130,2300,18.89,.282,.1,.01,7.35,2.8,.127,0,12.68,0
    1,2001,130,2400,18.68,.277,.1,.01,7.36,2.7,1.347,0,13.47,12.75
    1,2001,131,100,18.45,.275,.1,.01,7.36,2.7,1.292,0,12.92,12.62

    """

    import numpy
    from datetime import datetime
    from time import strptime

    # get sample datetime from filename
    fn = sensor_info['fn']
    sample_dt_start = filt_datetime(fn)

    # how many samples
    nsamp = 0
    for line in lines:
        m=re.search("^1,", line)
        if m:
            nsamp=nsamp+1

    N = nsamp
    data = {
        'dt' : numpy.array(numpy.ones((N,), dtype=object)*numpy.nan),
        'time' : numpy.array(numpy.ones((N,), dtype=long)*numpy.nan),
        'rain' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'press' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'press_wl' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'press_flow' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'press_csi_ft' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'press_csi_cfs' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        }

    # sample count
    i = 0

    for line in lines:
        csi = []
        # split line and parse float and integers
        m=re.search("^1,", line)
        if m:
            sw = re.split(',', line)
        else:
            continue

        # split line and parse float and integers
        sw = re.split(',', line)
        for s in sw:
            m = re.search(REAL_RE_STR, s)
            if m:
                csi.append(float(m.groups()[0]))

        if len(csi)==14:
            # get sample datetime from data
            yyyy = csi[1]
            yday = csi[2]
            (MM, HH) = math.modf(csi[3]/100.)
            MM = math.ceil(MM*100.)
            if (HH == 24):
                yday=yday+1
                HH = 0.
                
            sample_str = '%04d-%03d %02d:%02d' % (yyyy, yday, HH, MM)
            if  sensor_info['utc_offset']:
                sample_dt = scanf_datetime(sample_str, fmt='%Y-%j %H:%M') + \
                            timedelta(hours=sensor_info['utc_offset'])
            else:
                sample_dt = scanf_datetime(sample_str, fmt='%Y-%j %H:%M')

            data['dt'][i] = sample_dt # sample datetime
            data['time'][i] = dt2es(sample_dt) # sample time in epoch seconds
            # 
            # data['wtemp'][i] =  csi[4] # water temperature (C)
            # data['cond'][i] = csi[5] # specific conductivity (mS/cm)
            # data['do_sat'][i] = csi[6]   # saturated dissolved oxygen (% air sat)
            # data['do_mg'][i] = csi[7]   # dissolved oxygen (mg/l)
            # data['ph'][i] = csi[8]   # ph
            # data['turb'][i] = csi[9] # turbidity (NTU)

            # no adcp's prior to March 2005
            # data['sontek_wl'][i] = csi[5] # sontek water level (ft) 
            # data['sontek_flow'][i] = csi[6] # sontek flow (cfs)

            data['press_csi_ft'][i] = csi[10] # pressure water level (ft) 
            data['rain'][i] =  csi[11] # 15 sec rain count ??
            data['press_csi_cfs'][i] = csi[12] # flow flow (cfs)
            # data['battvolts'][i] = csi[13]   # battery (volts)
            
            i=i+1

        # if-elif
    # for line

    # revert  press_csi_ft back  to raw  pressure  reading (eventually
    # want csi to just report the  raw pressure reading so we can just
    # do this ourselves.
    data['press'] = (data['press_csi_ft']+1.5)/27.6778 # raw pressure (psi)
    # convert psi to height of water column based on hydrostatic eqn
    data['press_wl'] = data['press']*2.3059+sensor_info['press_offset'] # (feet)
    
    # flow based on parameter as computed by data logger
    # data['press_flow'] = data['press_csi_cfs']
                                
    # flow based on calculation from data logger but applied to offset calibration
    # SMH does not know what equation is based on or how these values are derived
    data['press_flow'] = ((data['press_wl']*12))*10.81 - 8.81 # cfs

    # check that no data[dt] is set to Nan or anything but datetime
    # keep only data that has a resolved datetime
    keep = numpy.array([type(datetime(1970,1,1)) == type(dt) for dt in data['dt'][:]])
    if keep.any():
        for param in data.keys():
            data[param] = data[param][keep]
            
    return data
 

def creator(platform_info, sensor_info, data):
    #
    # 
    title_str = sensor_info['description']+' at '+ platform_info['location']
    global_atts = { 
        'title' : title_str,
        'institution' : 'Unversity of North Carolina at Chapel Hill (UNC-CH)',
        'institution_url' : 'http://nccoos.unc.edu',
        'institution_dods_url' : 'http://nccoos.unc.edu',
        'metadata_url' : 'http://nccoos.unc.edu',
        'references' : 'http://nccoos.unc.edu',
        'contact' : 'Sara Haines (haines@email.unc.edu)',
        'station_owner' : 'Environment, Health, and Safety Office',
        'station_contact' : 'Sharon Myers (samyers@ehs.unc.edu)',
        # 
        'source' : 'fixed-observation',
        'history' : 'raw2proc using ' + sensor_info['process_module'],
        'comment' : 'File created using pycdf'+pycdfVersion()+' and numpy '+pycdfArrayPkg(),
        # conventions
        'Conventions' : 'CF-1.0; SEACOOS-CDL-v2.0',
        # SEACOOS CDL codes
        'format_category_code' : 'fixed-point',
        'institution_code' : platform_info['institution'],
        'platform_code' : platform_info['id'],
        'package_code' : sensor_info['id'],
        # institution specific
        'project' : 'Environment, Health, and Safety (EHS)',
        'project_url' : 'http://ehs.unc.edu/environment/water_quality',
        # timeframe of data contained in file yyyy-mm-dd HH:MM:SS
        # first date in monthly file
        'start_date' : data['dt'][0].strftime("%Y-%m-%d %H:%M:%S"),
        # last date in monthly file
        'end_date' : data['dt'][-1].strftime("%Y-%m-%d %H:%M:%S"), 
        'release_date' : now_dt.strftime("%Y-%m-%d %H:%M:%S"),
        #
        'creation_date' : now_dt.strftime("%Y-%m-%d %H:%M:%S"),
        'modification_date' : now_dt.strftime("%Y-%m-%d %H:%M:%S"),
        'process_level' : 'level1',
        #
        # must type match to data (e.g. fillvalue is real if data is real)
        '_FillValue' : -99999.,
        }

    var_atts = {
        # coordinate variables
        'time' : {'short_name': 'time',
                  'long_name': 'Time',
                  'standard_name': 'time',
                  'units': 'seconds since 1970-1-1 00:00:00 -0', # UTC
                  'axis': 'T',
                  },
        'lat' : {'short_name': 'lat',
             'long_name': 'Latitude',
             'standard_name': 'latitude',
             'reference':'geographic coordinates',
             'units': 'degrees_north',
             'valid_range':(-90.,90.),
             'axis': 'Y',
             },
        'lon' : {'short_name': 'lon',
                 'long_name': 'Longitude',
                 'standard_name': 'longitude',
                 'reference':'geographic coordinates',
                 'units': 'degrees_east',
                 'valid_range':(-180.,180.),
                 'axis': 'Y',
                 },
        'z' : {'short_name': 'z',
               'long_name': 'Altitude',
               'standard_name': 'altitude',
               'reference':'zero at mean sea level',
               'positive' : 'up',
               'units': 'm',
               'axis': 'Z',
               },
        # data variables
        'rain': {'short_name': 'rain',
                 'long_name': '15-Minute Rain',
                 'standard_name': 'rain',                          
                 'units': 'inches',
                  },
        'press_wl': { 'short_name': 'press_wl',
                  'long_name': 'Pressure Water Level',
                  'standard_name': 'water_level',                          
                  'units': 'feet',
                  'reference':'zero at station altitude',
                  'positive' : 'up',
                  },
        'press_flow': { 'short_name': 'flow',
                        'long_name': 'Pressure Stream Flow',
                        'standard_name': 'water_flux',                          
                        'units': 'cfs',
                        },
        }

    # dimension names use tuple so order of initialization is maintained
    dim_inits = (
        ('ntime', NC.UNLIMITED),
        ('nlat', 1),
        ('nlon', 1),
        ('nz', 1),
        )
    
    # using tuple of tuples so order of initialization is maintained
    # using dict for attributes order of init not important
    # use dimension names not values
    # (varName, varType, (dimName1, [dimName2], ...))
    var_inits = (
        # coordinate variables
        ('time', NC.INT, ('ntime',)),
        ('lat', NC.FLOAT, ('nlat',)),
        ('lon', NC.FLOAT, ('nlon',)),
        ('z',  NC.FLOAT, ('nz',)),
        # data variables
        ('rain', NC.FLOAT, ('ntime',)),
        ('press_wl', NC.FLOAT, ('ntime',)),
        ('press_flow', NC.FLOAT, ('ntime',)),
        )

    # subset data only to month being processed (see raw2proc.process())
    i = data['in']
    
    # var data 
    var_data = (
        ('lat',  platform_info['lat']),
        ('lon', platform_info['lon']),
        ('z', platform_info['altitude']),
        #
        ('time', data['time'][i]),
        #
        ('rain', data['rain'][i]),
        ('press_wl', data['press_wl'][i]),
        ('press_flow', data['press_flow'][i]),
        )

    return (global_atts, var_atts, dim_inits, var_inits, var_data)

def updater(platform_info, sensor_info, data):
    #
    global_atts = { 
        # update times of data contained in file (yyyy-mm-dd HH:MM:SS)
        # last date in monthly file
        'end_date' : data['dt'][-1].strftime("%Y-%m-%d %H:%M:%S"), 
        'release_date' : now_dt.strftime("%Y-%m-%d %H:%M:%S"),
        #
        'modification_date' : now_dt.strftime("%Y-%m-%d %H:%M:%S"),
        }

    # data variables
    # update any variable attributes like range, min, max
    var_atts = {}
    # var_atts = {
    #    'wtemp': {'max': max(data.u),
    #          'min': min(data.v),
    #          },
    #    'cond': {'max': max(data.u),
    #          'min': min(data.v),
    #          },
    #    }
    
    # subset data only to month being processed (see raw2proc.process())
    i = data['in']

    # data 
    var_data = (
        ('time', data['time'][i]),
        #
        ('rain', data['rain'][i]),
        ('press_wl', data['press_wl'][i]),
        ('press_flow', data['press_flow'][i]),
        )

    return (global_atts, var_atts, var_data)
#
