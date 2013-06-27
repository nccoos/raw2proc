#!/usr/bin/env python
# Last modified:  Time-stamp: <2010-12-09 16:14:19 haines>
"""
how to parse data, and assert what data and info goes into
creating and updating monthly netcdf files

parse data water quality data from ysi 6600 V2
collected on Campbell Scientific DataLogger (loggernet) (csi)

parser : sample date and time, 
         water temperature, conductivity, pH, dissolved oxygen, turbidity, and system battery

creator : lat, lon, z, time, wtemp, cond, ph, turb, do_sat, do_mg, battvolts 
updator : time, wtemp, cond, ph, turb, do_sat, do_mg, battvolts 


Examples
--------

>> (parse, create, update) = load_processors('proc_csi_wq_v2')
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
    

    """
    import numpy
    from datetime import datetime
    from time import strptime
    import math

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
        'wtemp' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'cond' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'do_sat' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'do_mg' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'ph' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'turb' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'battvolts' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
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
            # if  sensor_info['utc_offset']:
            #     sample_dt = scanf_datetime(sample_str, fmt='%m-%d-%Y %H:%M:%S') + \
            #                 timedelta(hours=sensor_info['utc_offset'])
            # else:
            sample_dt = scanf_datetime(sample_str, fmt='%Y-%j %H:%M')

            data['dt'][i] = sample_dt # sample datetime
            data['time'][i] = dt2es(sample_dt) # sample time in epoch seconds
            # 
            data['wtemp'][i] =  csi[4] # water temperature (C)
            data['cond'][i] = csi[5] # specific conductivity (mS/cm)
            data['do_sat'][i] = csi[6]   # saturated dissolved oxygen (% air sat)
            data['do_mg'][i] = csi[7]   # dissolved oxygen (mg/l)
            data['ph'][i] = csi[8]   # ph
            data['turb'][i] = csi[9] # turbidity (NTU)

            # no adcp's prior to March 2005
            # data['sontek_wl'][i] = csi[5] # sontek water level (ft) 
            # data['sontek_flow'][i] = csi[6] # sontek flow (cfs)

            # data['press_wl'][i] = csi[10] # pressure water level (ft ?? or inches) 
            # data['rain'][i] =  csi[11] # 15 sec rain count ??
            # data['press_flow'][i] = csi[12] # flow flow (cfs)
            data['battvolts'][i] = csi[13]   # battery (volts)

            i=i+1

        # if-elif
    # for line

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
        'references' : 'http://ehs.unc.edu',
        'contact' : 'Sara Haines (haines@email.unc.edu)',
        'station_owner' : 'Environment, Health, and Safety Office',
        'station_contact' : 'Sharon Myers (samyers@ehs.unc.edu)',
        # 
        'source' : 'fixed-point observation',
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
               'long_name': 'Height',
               'standard_name': 'height',
               'reference':'zero at sea-surface',
               'positive' : 'up',
               'units': 'm',
               'axis': 'Z',
               },
        # data variables
        'wtemp': {'short_name': 'wtemp',
                  'long_name': 'Water Temperature',
                  'standard_name': 'water_temperature',                          
                  'units': 'degrees_Celsius',
                  },
        'cond': {'short_name': 'cond',
                 'long_name': 'Conductivity',
                 'standard_name': 'conductivity',                          
                 'units': 'mS cm-1',
                 },
        'turb': {'short_name': 'turb',
                 'long_name': 'Turbidity',
                 'standard_name': 'turbidity',                          
                 'units': 'NTU',
                 },
        'ph': {'short_name': 'ph',
               'long_name': 'pH',
               'standard_name': 'ph',                          
               'units': '',
               },
        'do_mg': {'short_name': 'do_mg',
               'long_name': 'ROX Optical Dissolved Oxygen, Derived Concentration',
               'standard_name': 'dissolved_oxygen_concentration',                          
               'units': 'mg l-1',
               },
        'do_sat': {'short_name': 'do_sat',
               'long_name': 'ROX Optical Dissolved Oxygen, Percent of Air Saturation',
               'standard_name': 'dissolved_oxygen_relative_to_air_saturation',                          
               'units': '%',
               },
        'battvolts': {'short_name': 'battery',
               'long_name': 'Battery Voltage of the Station',
               'standard_name': 'battery_voltage',                          
               'units': 'volts',
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
        ('wtemp', NC.FLOAT, ('ntime',)),
        ('cond', NC.FLOAT, ('ntime',)),
        ('turb', NC.FLOAT, ('ntime',)),
        ('ph', NC.FLOAT, ('ntime',)),
        ('do_mg', NC.FLOAT, ('ntime',)),
        ('do_sat', NC.FLOAT, ('ntime',)),
        ('battvolts', NC.FLOAT, ('ntime',)),
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
        ('wtemp', data['wtemp'][i]),
        ('cond', data['cond'][i]),
        ('turb', data['turb'][i]),
        ('ph', data['ph'][i]),
        ('do_mg', data['do_mg'][i]),
        ('do_sat', data['do_sat'][i]),
        ('battvolts', data['battvolts'][i]),
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
        ('wtemp', data['wtemp'][i]),
        ('cond', data['cond'][i]),
        ('turb', data['turb'][i]),
        ('ph', data['ph'][i]),
        ('do_mg', data['do_mg'][i]),
        ('do_sat', data['do_sat'][i]),
        ('battvolts', data['battvolts'][i]),
        )

    return (global_atts, var_atts, var_data)
#
