"""
Parse data and assert what data creates and updates monthly NetCDF files.

Spongenet mini_andi conductivity parameters sponge data.
"""

import math
import numpy as n
import pycdf
import datetime
import procutil
from spongenet.parse import Data

nowDt = datetime.datetime.utcnow().replace(microsecond=0)

def parser(platform_info, sensor_info, lines):
    """
    Parse and assign sponge data from XML file.
    """
    
    _data = Data(''.join(lines))
    
    # Each Device tag represents a time sample.
    num_samples = len(_data.devices)
    
    data = {
        'dt'           : n.array(n.ones((num_samples,)) * n.nan, dtype=object),
        'time'         : n.array(n.ones((num_samples,)) * n.nan, dtype=long),
        'pdt'          : n.array(n.ones((num_samples,)) * n.nan, dtype=object),
        'ptime'        : n.array(n.ones((num_samples,)) * n.nan, dtype=long),
        'ds'           : n.array(n.ones((num_samples,)) * n.nan, dtype=object),
        'session'      : n.array(n.ones((num_samples,)) * n.nan, dtype=long),
        'pds'          : n.array(n.ones((num_samples,)) * n.nan, dtype=object),
        'psession'     : n.array(n.ones((num_samples,)) * n.nan, dtype=long),
        'record'       : n.array(n.ones((num_samples,)) * n.nan, dtype=int),
        'status'       : n.array(n.ones((num_samples,)) * n.nan, dtype=int),
        'pstatus'      : n.array(n.ones((num_samples,)) * n.nan, dtype=int),
        'conductivity' : n.array(n.ones((num_samples,)) * n.nan, dtype=float),
        'temperature'  : n.array(n.ones((num_samples,)) * n.nan, dtype=float),
           }
    
    for (sample_index, sample) in enumerate(_data.devices):
        # sample time at the platform
        dt = {'month' : int(sample['time'][5:7]),
              'day'   : int(sample['time'][8:10]),
              'year'  : int(sample['time'][0:4]),
              'hour'  : int(sample['time'][11:13]),
              'min'   : int(sample['time'][14:16]),
              'sec'   : int(sample['time'][17:19]),
             }
        dt = '%(month)02d-%(day)02d-%(year)04d %(hour)02d:%(min)02d:%(sec)02d' \
             % dt
        dt = procutil.scanf_datetime(dt, fmt='%m-%d-%Y %H:%M:%S')
        if sensor_info['utc_offset']:
            dt = dt + datetime.timedelta(hours=sensor_info['utc_offset'])
        data['dt'][sample_index] = dt        
        data['time'][sample_index] = procutil.dt2es(dt)

        # sample time at the package
        package_dt = {'month' : int(sample['data_time'][5:7]),
                      'day'   : int(sample['data_time'][8:10]),
                      'year'  : int(sample['data_time'][0:4]),
                      'hour'  : int(sample['data_time'][11:13]),
                      'min'   : int(sample['data_time'][14:16]),
                      'sec'   : int(sample['data_time'][17:19]),
                     }
        package_dt = ('%(month)02d-%(day)02d-%(year)04d ' +
                      '%(hour)02d:%(min)02d:%(sec)02d') \
                     % package_dt
        package_dt = procutil.scanf_datetime(package_dt, fmt='%m-%d-%Y %H:%M:%S')
        if sensor_info['utc_offset']:
            package_dt = package_dt + \
                        datetime.timedelta(hours=sensor_info['utc_offset'])
        data['pdt'][sample_index] = package_dt
        data['ptime'][sample_index] = procutil.dt2es(package_dt)

        # platform session time
        ds = {'month' : int(sample['sessionid'][14:16]),
              'day'   : int(sample['sessionid'][17:19]),
              'year'  : int(sample['sessionid'][9:13]),
              'hour'  : int(sample['sessionid'][20:22]),
              'min'   : int(sample['sessionid'][23:25]),
              'sec'   : int(sample['sessionid'][26:28]),
             }
        ds = '%(month)02d-%(day)02d-%(year)04d %(hour)02d:%(min)02d:%(sec)02d' \
             % ds
        ds = procutil.scanf_datetime(ds, fmt='%m-%d-%Y %H:%M:%S')
        if sensor_info['utc_offset']:
            ds = ds + datetime.timedelta(hours=sensor_info['utc_offset'])
        data['ds'][sample_index] = ds        
        data['session'][sample_index] = procutil.dt2es(ds)

        # package session time
        package_ds = {'month' : int(sample['data_sessionid'][5:7]),
                      'day'   : int(sample['data_sessionid'][8:10]),
                      'year'  : int(sample['data_sessionid'][0:4]),
                      'hour'  : int(sample['data_sessionid'][11:13]),
                      'min'   : int(sample['data_sessionid'][14:16]),
                      'sec'   : int(sample['data_sessionid'][17:19]),
                     }
        package_ds = ('%(month)02d-%(day)02d-%(year)04d ' +
                      '%(hour)02d:%(min)02d:%(sec)02d') \
                     % package_ds
        package_ds = procutil.scanf_datetime(package_ds, fmt='%m-%d-%Y %H:%M:%S')
        if sensor_info['utc_offset']:
            package_ds = package_ds + \
                        datetime.timedelta(hours=sensor_info['utc_offset'])
        data['pds'][sample_index] = package_ds
        data['psession'][sample_index] = procutil.dt2es(package_ds)

        # platform variables
        try:
            data['record'][sample_index] = int(sample["recordnumber"])
        except KeyError:
            pass

        try:
            data['status'][sample_index] = int(sample["status"].
                                               partition(":")[0])
        except (KeyError, AttributeError, ):
            pass

        # package variables
        try:
            data['pstatus'][sample_index] = int(sample.sensors
                                                [sensor_info["id_number"]]
                                                ["status"].
                                                partition(":")[0])
        except (KeyError, AttributeError, ):
            pass

        try:
            data['conductivity'][sample_index] = float(sample.sensors
                                                 [sensor_info["id_number"]].
                                                 points[sensor_info
                                                 ["conductivity_description"]]
                                                 ["value"])
        except (KeyError, AttributeError, ):
            pass

        try:
            data['temperature'][sample_index] = float(sample.sensors
                                                [sensor_info["id_number"]].
                                                points[sensor_info
                                                ["temperature_description"]]
                                                ["value"])
        except (KeyError, AttributeError, ):
            pass

    return data

def creator(platform_info, sensor_info, data):
    #
    # 
    title_str = sensor_info['description']+' at '+ sensor_info['location']
    global_atts = { 
        # Required
        'title' : title_str,
        'institution' : platform_info['institution'],
        'institution_url' : platform_info['institution_url'],
        'institution_dods_url' : platform_info['institution_dods_url'],
        'contact' : platform_info['contact'],
        'Conventions' : platform_info['conventions'],
        # Required by Scout
        'format_category_code' : platform_info['format_category_code'],
        'institution_code' : platform_info['institution_code'],
        'platform_code' : platform_info['id'],
        'package_code' : sensor_info['id'],
        # Required by Version tracking
        'format' : platform_info['format'],
        'seacoos_rt_version' : platform_info['seacoos_rt_version'],
        # Recommended
        '_FillValue' : n.nan,
        'missing_value' : n.nan,
        'source' : platform_info['source'],
        'references' : platform_info['references'],
        'metadata_url' : platform_info['metadata_url'],
        'history' : 'raw2proc using ' + sensor_info['process_module'],
        'comment' : 'File created using pycdf ' + \
                    pycdf.pycdfVersion() + ' and ' + \
                    pycdf.pycdfArrayPkg() + ' ' + \
                    n.__version__,
        'project' : platform_info['project'],
        'project_url' : platform_info['project_url'],
        # timeframe of data contained in file yyyy-mm-dd HH:MM:SS
        # first date in monthly file
        'start_date' : data['dt'][0].strftime("%Y-%m-%d %H:%M:%S"),
        # last date in monthly file
        'end_date' : data['dt'][-1].strftime("%Y-%m-%d %H:%M:%S"), 
        'release_date' : nowDt.strftime("%Y-%m-%d %H:%M:%S"),
        'creation_date' : nowDt.strftime("%Y-%m-%d %H:%M:%S"),
        'modification_date' : nowDt.strftime("%Y-%m-%d %H:%M:%S"),
        'process_level' : 'level1',
        # Custom
        'id_number' : platform_info['id_number'],
        'description' : platform_info['description'],
        'serial_number' : platform_info['serial_number'],
        'product_number' : platform_info['product_number'],
        'product_name' : platform_info['product_name'],
        'type' : platform_info['type'],
        'protocol_version' : platform_info['protocol_version'],
        'xmlns' : platform_info['xmlns'],
        'location' : platform_info['location'],
        'vertical_position': platform_info['vertical_position'],
        'owner' : platform_info['owner'],
        'package_id_number' : sensor_info['id_number'],
        'package_description' : sensor_info['description'],
        'package_serial_number' : sensor_info['serial_number'],
        'package_product_number' : sensor_info['product_number'],
        'package_product_name' : sensor_info['product_name'],
        'package_adr' : sensor_info['adr'],
        'package_protocol_version' : sensor_info['protocol_version'],
        'package_vertical_position' : sensor_info['vertical_position'],
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
               'units': 'meters',
               'axis': 'Z',
              },
        # data variables
        'ptime' : {'short_name': 'ptime',
                   'long_name': 'Package Time',
                   'standard_name': 'none',
                   'units': 'seconds since 1970-1-1 00:00:00 -0', # UTC
                 },
        'session' : {'short_name': 'session',
                     'long_name': 'Session ID',
                     'standard_name': 'none',
                     'units': 'seconds since 1970-1-1 00:00:00 -0', # UTC
                 },
        'psession' : {'short_name': 'ptime',
                      'long_name': 'Package Session ID',
                      'standard_name': 'none',
                      'units': 'seconds since 1970-1-1 00:00:00 -0', # UTC
                 },
        'record' : {'short_name': 'record',
                    'long_name': 'Record Number',
                    'standard_name': 'none',
                    'units' : 'none',
                 },
        'status': {'short_name' : 'status',
                   'long_name': 'Platform Status Code',
                   'standard_name': 'none',
                   'units' : 'none',
                   'value_map' : platform_info['status_map'],
                  },
        'pstatus': {'short_name' : 'pstatus',
                    'long_name': 'Package Status Code',
                    'standard_name': 'none',
                    'units' : 'none',
                    'value_map' : sensor_info['status_map'],
                  },
        'conductivity' : {'short_name' : 'conductivity',
                    'long_name': sensor_info['conductivity_description'],
                    'standard_name': 'conductivity',
                    'units': 'none',
                    'id_number' : sensor_info['conductivity_id'],
                    'type' : sensor_info['conductivity_type'],
                    'format' : sensor_info['conductivity_format'],
                    'non_standard_units' : sensor_info['conductivity_units'],
                    'range_min' : sensor_info['conductivity_range_min'],
                    'range_max' : sensor_info['conductivity_range_max'],
                         },
        'temperature' : {'short_name' : 'temperature',
                    'long_name': sensor_info['temperature_description'],
                    'standard_name': 'water_temperature',
                    'units': 'celsius',
                    'id_number' : sensor_info['temperature_id'],
                    'type' : sensor_info['temperature_type'],
                    'format' : sensor_info['temperature_format'],
                    'non_standard_units' : sensor_info['temperature_units'],
                    'range_min' : sensor_info['temperature_range_min'],
                    'range_max' : sensor_info['temperature_range_max'],
                        },
        }
    
    # dimension names use tuple so order of initialization is maintained
    dim_inits = (
        ('ntime', pycdf.NC.UNLIMITED),
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
        ('time',  pycdf.NC.INT,   ('ntime',)),
        ('lat',   pycdf.NC.FLOAT, ('nlat',)),
        ('lon',   pycdf.NC.FLOAT, ('nlon',)),
        ('z',     pycdf.NC.FLOAT, ('nz',)),
        # data variables
        ('ptime',        pycdf.NC.INT, ('ntime',)),
        ('session',      pycdf.NC.INT, ('ntime',)),
        ('psession',     pycdf.NC.INT, ('ntime',)),
        ('record',       pycdf.NC.INT, ('ntime',)),
        ('status',       pycdf.NC.INT, ('ntime',)),
        ('pstatus',      pycdf.NC.INT, ('ntime',)),
        ('conductivity', pycdf.NC.FLOAT, ('ntime',)),
        ('temperature',  pycdf.NC.FLOAT, ('ntime',)),
                )
    
    # subset data only to month being processed (see raw2proc.process())
    i = data['in']
    
    # var data 
    var_data = (
        ('time',         data['time'][i]),
        ('lat',          sensor_info['lat']),
        ('lon',          sensor_info['lat']),
        ('z',            sensor_info['elevation']),
        ('ptime',        data['ptime'][i]),
        ('session',      data['session'][i]),
        ('psession',     data['psession'][i]),
        ('record',       data['record'][i]),
        ('status',       data['status'][i]),
        ('pstatus',      data['pstatus'][i]),
        ('conductivity', data['conductivity'][i]),
        ('temperature',  data['temperature'][i]),
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
        ('time',         data['time'][i]),
        ('ptime',        data['ptime'][i]),
        ('session',      data['session'][i]),
        ('psession',     data['psession'][i]),
        ('record',       data['record'][i]),
        ('status',       data['status'][i]),
        ('pstatus',      data['pstatus'][i]),
        ('conductivity', data['conductivity'][i]),
        ('temperature',  data['temperature'][i]),
        )
    
    return (global_atts, var_atts, var_data)
