#!/usr/bin/env python
# Last modified:  Time-stamp: <2010-12-09 16:14:55 haines>
"""
how to parse data, and assert what data and info goes into
creating and updating monthly netcdf files

parse data water level and flow data (sontek argonaut and pressure
sensor) collected on Campbell Scientific DataLogger (loggernet) (csi)

parser : sample date and time, water_depth and flow from sontek and pressure

creator : lat, lon, z, time, sontek_wl, sontek_flow, press_wl, press_flow
updator : time, sontek_wl, sontek_flow, press_wl, press_flow


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
    
    Example data: NO Sontek

    TOA5,CR1000_CBC,CR1000,5498,CR1000.Std.11,CPU:UNC_CrowBranch.CR1,1554,Data15Min
    TIMESTAMP,RECORD,RainIn_Tot,WaterLevelFt,Flow
    TS,RN,,,
    ,,Tot,Smp,Smp
    2009-01-22 15:30:00,0,0,0,0
    2009-01-22 15:45:00,1,0,0,0
    2009-01-22 16:00:00,2,0.01,0,0
    2009-01-22 16:15:00,3,0,0,0

    Example data: with Sontek

    """

    import numpy
    from datetime import datetime
    from time import strptime

    # get sample datetime from filename
    fn = sensor_info['fn']
    sample_dt_start = filt_datetime(fn)

    # how many samples (don't count header 4 lines)
    nsamp = len(lines[4:])

    N = nsamp
    data = {
        'dt' : numpy.array(numpy.ones((N,), dtype=object)*numpy.nan),
        'time' : numpy.array(numpy.ones((N,), dtype=long)*numpy.nan),
        'rain' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'sontek_wl' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'sontek_flow' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'press' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'press_wl' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'press_flow' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'press_csi_ft' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'press_csi_cfs' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
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

        # replace any "NAN" text with a number
        for index, s in enumerate(sw):
            m = re.search(NAN_RE_STR, s)
            if m:
                sw[index] = '-99999'

        # parse date-time, and all other float and integers
        for s in sw[1:]:
            m = re.search(REAL_RE_STR, s)
            if m:
                csi.append(float(m.groups()[0]))

        if  sensor_info['utc_offset']:
            sample_dt = scanf_datetime(sw[0], fmt='"%Y-%m-%d %H:%M:%S"') + \
                        timedelta(hours=sensor_info['utc_offset'])
        else:
            sample_dt = scanf_datetime(sw[0], fmt='"%Y-%m-%d %H:%M:%S"')

        data['dt'][i] = sample_dt # sample datetime
        data['time'][i] = dt2es(sample_dt) # sample time in epoch seconds
        
        # SMH -- 2009-12-05 modification
        # press_csi water level and flow conversion on the data logger is not correct
        # this will be reverted to original pressure reading and wl and flow recomputed.
        if len(csi)==6:
            # MOW has all six fields but no sontek now
            data['rain'][i] =  csi[1] # 15 min rain count (inches)
            # data['sontek_wl'][i] = csi[2] # sontek water level (ft) 
            # data['sontek_flow'][i] = csi[3] # sontek flow (cfs)
            data['press_csi_ft'][i] = csi[4] # csi reported pressure water level (ft) 
            data['press_csi_cfs'][i] = csi[5] # csi reported flow (cfs)
            i=i+1
        elif len(csi)==4:
            # CBC is not reporting pressure level and flow -- no pressure sensor!
            data['rain'][i] =  csi[1] # 15 min rain count (inches)
            data['sontek_wl'][i] = csi[2] # sontek water level (ft) 
            data['sontek_flow'][i] = csi[3] # sontek flow (cfs)
            i=i+1
        else:
            print ' ... skipping line %d -- %s ' % (i,line)
            continue

        # if re.search
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
        'sontek_wl': {'short_name': 'sontek_wl',
                  'long_name': 'Sontek Water Level',
                  'standard_name': 'water_level',                          
                  'units': 'feet',
                  'reference':'zero at station altitude',
                  'positive' : 'up',
                  },
        'sontek_flow': {'short_name': 'flow',
                        'long_name': 'Sontek Stream Flow',
                        'standard_name': 'water_flux',                          
                        'units': 'cfs',
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
        ('sontek_wl', NC.FLOAT, ('ntime',)),
        ('sontek_flow', NC.FLOAT, ('ntime',)),
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
        ('sontek_wl', data['sontek_wl'][i]),
        ('sontek_flow', data['sontek_flow'][i]),
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
        ('sontek_wl', data['sontek_wl'][i]),
        ('sontek_flow', data['sontek_flow'][i]),
        ('press_wl', data['press_wl'][i]),
        ('press_flow', data['press_flow'][i]),
        )

    return (global_atts, var_atts, var_data)
#
