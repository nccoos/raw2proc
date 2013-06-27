"""
Parse data and assert what data creates and updates monthly NetCDF files.

Scintec SFAS processed sodar wind profile data.
"""

import math
import numpy as n
import pycdf
import datetime
import procutil
from sodar.scintec import maindata

nowDt = datetime.datetime.utcnow().replace(microsecond=0)
manual = ['z','speed','dir','error']

def parser(platform_info, sensor_info, lines):
    """
    Parse and assign wind profile data from main Sodar file.
    """
    
    main_data = maindata.MainData(''.join(lines))
    
    num_profiles       = len(main_data)
    min_altitude      = sensor_info['min_altitude']
    altitude_interval = sensor_info['altitude_interval']
    num_altitudes     = sensor_info['num_altitudes']
    sensor_elevation  = sensor_info['sensor_elevation']
    
    altitudes = [(altitude_num * altitude_interval) + min_altitude
                  for altitude_num in range(num_altitudes)]
    elevations  = [altitude + sensor_elevation for altitude in altitudes]
    
    data = {
        'dt'   : n.array(n.ones((num_profiles,), dtype=object) * n.nan),
        'time' : n.array(n.ones((num_profiles,), dtype=long) * n.nan),
        'z'    : n.array(elevations, dtype=float),
        'u'    : n.array(n.ones((num_profiles,
                                 num_altitudes), dtype=float) * n.nan),
        'v'    : n.array(n.ones((num_profiles,
                                 num_altitudes), dtype=float) * n.nan),
           }
    
    gaps = {}
    for variable in main_data.variables:
        symbol = variable['symbol']
        gaps[symbol] = variable['gap']   
        if symbol not in manual:
            data[symbol.lower()] = n.array(n.ones((num_profiles,
                                                   num_altitudes),
                                                  dtype=float) * n.nan)
    
    data['error'] = n.array(n.ones((num_profiles,
                                    num_altitudes), dtype = int) * n.nan)
    for (profile_index, profile) in enumerate(main_data):
        dt = {'month' : profile.stop.month,
              'day'   : profile.stop.day,
              'year'  : profile.stop.year,
              'hour'  : profile.stop.hour,
              'min'   : profile.stop.minute,
             }
        dt = '%(month)02d-%(day)02d-%(year)04d %(hour)02d:%(min)02d' % dt
        dt = procutil.scanf_datetime(dt, fmt='%m-%d-%Y %H:%M')
        if sensor_info['utc_offset']:
            dt = dt + datetime.timedelta(hours=sensor_info['utc_offset'])
        data['dt'][profile_index] = dt
        
        data['time'][profile_index] = procutil.dt2es(dt)
        
        for (observation_index, observation) in enumerate(profile):
            radial = observation['speed']
            theta  = observation['dir']
            
            if radial != gaps['speed'] and theta != gaps['dir']:
                theta  = math.pi * float(theta) / 180.0
                radial = float(radial)
                data['u'][profile_index][observation_index] = \
                    radial * math.sin(theta)
                data['v'][profile_index][observation_index] = \
                    radial * math.cos(theta)
            
            for variable in profile.variables:
               if variable not in manual and \
               observation[variable] != gaps[variable]:
                   data[variable.lower()][profile_index][observation_index] = \
                       float(observation[variable])
            
            data['error'][profile_index][observation_index] = \
                int(observation['error'])
    
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
        'contact' : 'cbc (cbc@unc.edu)',
        # 
        'source' : 'fixed-profiler (acoustic doppler) observation',
        'history' : 'raw2proc using ' + sensor_info['process_module'],
        'comment' : 'File created using pycdf'+pycdf.pycdfVersion()+' and numpy '+pycdf.pycdfArrayPkg(),
        # conventions
        'Conventions' : 'CF-1.0; SEACOOS-CDL-v2.0',
        # SEACOOS CDL codes
        'format_category_code' : 'fixed-profiler',
        'institution_code' : platform_info['institution'],
        'platform_code' : platform_info['id'],
        'package_code' : sensor_info['id'],
        # institution specific
        'project' : 'North Carolina Coastal Ocean Observing System (NCCOOS)',
        'project_url' : 'http://nccoos.unc.edu',
        # timeframe of data contained in file yyyy-mm-dd HH:MM:SS
        # first date in monthly file
        'start_date' : data['dt'][0].strftime("%Y-%m-%d %H:%M:%S"),
        # last date in monthly file
        'end_date' : data['dt'][-1].strftime("%Y-%m-%d %H:%M:%S"), 
        'release_date' : nowDt.strftime("%Y-%m-%d %H:%M:%S"),
        #
        'creation_date' : nowDt.strftime("%Y-%m-%d %H:%M:%S"),
        'modification_date' : nowDt.strftime("%Y-%m-%d %H:%M:%S"),
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
                 'long_name': 'Longtitude',
                 'standard_name': 'longtitude',
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
        'u': {'short_name' : 'u',
              'long_name': 'East/West Component of Wind',
              'standard_name': 'eastward_wind',
              'units': 'm s-1',
             },
        'v': {'short_name' : 'v',
              'long_name': 'North/South Component of Wind',
              'standard_name': 'northward_wind',                          
              'units': 'm s-1',
             },
        'w': {'short_name' : 'w',
              'long_name': 'Vertical Component of Wind',
              'standard_name': 'upward_wind',                          
              'units': 'm s-1',
             },
        'sigw': {'short_name' : 'sigw',
                 'long_name': 'Standard Deviation of Vertical Component',
                 'standard_name': 'sigma_upward_wind',
                },
        'bck' : {'short_name': 'bck',
                 'long_name': 'Backscatter',
                 'standard_name': 'backscatter'
                },
        'error' : {'short_name': 'error',
                   'long_name': 'Error Code',
                   'standard_name': 'error_code'
                  },
        }
    
    # dimension names use tuple so order of initialization is maintained
    dim_inits = (
        ('ntime', pycdf.NC.UNLIMITED),
        ('nlat', 1),
        ('nlon', 1),
        ('nz', sensor_info['num_altitudes'])
        )
    
    # using tuple of tuples so order of initialization is maintained
    # using dict for attributes order of init not important
    # use dimension names not values
    # (varName, varType, (dimName1, [dimName2], ...))
    var_inits = (
        # coordinate variables
        ('time',  pycdf.NC.INT,   ('ntime',)),
        ('lat',   pycdf.NC.FLOAT, ('nlat',)),
        ('lon',   pycdf.NC.FLOAT, ('nlon',)),
        ('z',     pycdf.NC.FLOAT, ('nz',)),
        # data variables
        ('u',     pycdf.NC.FLOAT, ('ntime', 'nz')),
        ('v',     pycdf.NC.FLOAT, ('ntime', 'nz')),
        ('w',     pycdf.NC.FLOAT, ('ntime', 'nz')),
        ('sigw',  pycdf.NC.FLOAT, ('ntime', 'nz')),
        ('bck',   pycdf.NC.FLOAT, ('ntime', 'nz')),
        ('error', pycdf.NC.INT,   ('ntime', 'nz')),
                )
    
    # subset data only to month being processed (see raw2proc.process())
    i = data['in']
    
    # var data 
    var_data = (
        ('time',  data['time'][i]),
        ('lat',   platform_info['lat']),
        ('lon',   platform_info['lon']),
        ('z',     data['z']),
        ('u',     data['u'][i]),
        ('v',     data['v'][i]),
        ('w',     data['w'][i]),
        ('sigw',  data['sigw'][i]),
        ('bck',   data['bck'][i]),
        ('error', data['error'][i]),
        )
    
    return (global_atts, var_atts, dim_inits, var_inits, var_data)

def updater(platform_info, sensor_info, data):
    #
    global_atts = { 
        # update times of data contained in file (yyyy-mm-dd HH:MM:SS)
        # last date in monthly file
        'end_date' : data['dt'][-1].strftime("%Y-%m-%d %H:%M:%S"), 
        'release_date' : nowDt.strftime("%Y-%m-%d %H:%M:%S"),
        #
        'modification_date' : nowDt.strftime("%Y-%m-%d %H:%M:%S"),
        }
    
    # data variables
    # update any variable attributes like range, min, max
    var_atts = {}
    
    # subset data only to month being processed (see raw2proc.process())
    i = data['in']
    
    # data 
    var_data = (
        ('time',  data['time'][i]),
        ('u',     data['u'][i]),
        ('v',     data['v'][i]),
        ('w',     data['w'][i]),
        ('sigw',  data['sigw'][i]),
        ('bck',   data['bck'][i]),
        ('error', data['error'][i]),
        )
    
    return (global_atts, var_atts, var_data)
