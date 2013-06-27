#!/usr/bin/env python
"""
Parse data and assert what data creates and updates monthly NetCDF files.

Remtech PA0 processed sodar wind profile data.
"""

import math
import numpy as n
import pycdf
import datetime
import procutil
from sodar.remtech import rawData

INVALID       = '-9999'

nowDt = datetime.datetime.utcnow().replace(microsecond=0)

def parser(platform_info, sensor_info, lines):
    """
    Parse and assign wind profile data from raw Sodar file.
    """
    
    rawDataObject = rawData.RawData(''.join(lines))
    
    numSamples       = len(rawDataObject)
    minAltitude      = sensor_info['min_altitude']
    altitudeInterval = sensor_info['altitude_interval']
    numAltitudes     = sensor_info['num_altitudes']
    sensorElevation  = sensor_info['sensor_elevation']
    
    altitudes = [(altitudeNum * altitudeInterval) + minAltitude
                  for altitudeNum in range(numAltitudes)]
    elevations  = [altitude + sensorElevation for altitude in altitudes]
    altitudes = [str(altitude) for altitude in altitudes]
    
    data = {
        'block'   : n.array(n.ones((numSamples,), dtype=int) * n.nan),
        'dt'      : n.array(n.ones((numSamples,), dtype=object) * n.nan),
        'time'    : n.array(n.ones((numSamples,), dtype=long) * n.nan),
        'val1'    : n.array(n.ones((numSamples,), dtype=int) * n.nan),
        'val2'    : n.array(n.ones((numSamples,), dtype=int) * n.nan),
        'val3'    : n.array(n.ones((numSamples,), dtype=int) * n.nan),
        'val4'    : n.array(n.ones((numSamples,), dtype=int) * n.nan),
        'spu1'    : n.array(n.ones((numSamples,), dtype=int) * n.nan),
        'spu2'    : n.array(n.ones((numSamples,), dtype=int) * n.nan),
        'spu3'    : n.array(n.ones((numSamples,), dtype=int) * n.nan),
        'spu4'    : n.array(n.ones((numSamples,), dtype=int) * n.nan),
        'nois1'   : n.array(n.ones((numSamples,), dtype=int) * n.nan),
        'nois2'   : n.array(n.ones((numSamples,), dtype=int) * n.nan),
        'nois3'   : n.array(n.ones((numSamples,), dtype=int) * n.nan),
        'nois4'   : n.array(n.ones((numSamples,), dtype=int) * n.nan),
        'femax'   : n.array(n.ones((numSamples,), dtype=int) * n.nan),
        'softw'   : n.array(n.ones((numSamples,), dtype=int) * n.nan),
        'fe11'    : n.array(n.ones((numSamples,), dtype=int) * n.nan),
        'fe12'    : n.array(n.ones((numSamples,), dtype=int) * n.nan),
        'fe21'    : n.array(n.ones((numSamples,), dtype=int) * n.nan),
        'fe22'    : n.array(n.ones((numSamples,), dtype=int) * n.nan),
        'snr1'    : n.array(n.ones((numSamples,), dtype=int) * n.nan),
        'snr2'    : n.array(n.ones((numSamples,), dtype=int) * n.nan),
        'snr3'    : n.array(n.ones((numSamples,), dtype=int) * n.nan),
        'snr4'    : n.array(n.ones((numSamples,), dtype=int) * n.nan),
        'check'   : n.array(n.ones((numSamples,), dtype=int) * n.nan),
        'jam'     : n.array(n.ones((numSamples,), dtype=int) * n.nan),
        'z'       : n.array(elevations, dtype=float),
        'u'       : n.array(n.ones((numSamples,
                                    numAltitudes), dtype=float) * n.nan), 
        'v'       : n.array(n.ones((numSamples,
                                    numAltitudes), dtype=float) * n.nan),
        'w'       : n.array(n.ones((numSamples,
                                    numAltitudes), dtype=float) * n.nan),
        'echo'    : n.array(n.ones((numSamples,
                                    numAltitudes), dtype = int) * n.nan),
        }
    
    for sample in rawDataObject:
        sampleIndex = rawDataObject.index(sample)
        
        data['block'][sampleIndex] = int(sample['BL#'])
                               
        dt = {'month' : int(sample['MONTH']),
              'day'   : int(sample['DAY']),
              'year'  : int(sample['YEAR']),
              'hour'  : int(sample['HOUR']),
              'min'   : int(sample['MIN']),
            }
        dt = '%(month)02d-%(day)02d-%(year)04d %(hour)02d:%(min)02d' % dt
        dt = procutil.scanf_datetime(dt, fmt='%m-%d-%Y %H:%M')
        if sensor_info['utc_offset']:
            dt = dt + datetime.timedelta(hours=sensor_info['utc_offset'])
        data['dt'][sampleIndex] = dt
        
        data['time'][sampleIndex] = procutil.dt2es(dt)
        
        data['val1'][sampleIndex] = int(sample['VAL1'])
        data['val2'][sampleIndex] = int(sample['VAL2'])
        data['val3'][sampleIndex] = int(sample['VAL3'])
        data['val4'][sampleIndex] = int(sample['VAL4'])
        
        data['spu1'][sampleIndex] = int(sample['SPU1'])
        data['spu2'][sampleIndex] = int(sample['SPU2'])
        data['spu3'][sampleIndex] = int(sample['SPU3'])
        data['spu4'][sampleIndex] = int(sample['SPU4'])
        
        data['nois1'][sampleIndex] = int(sample['NOIS1'])
        data['nois2'][sampleIndex] = int(sample['NOIS2'])
        data['nois3'][sampleIndex] = int(sample['NOIS3'])
        data['nois4'][sampleIndex] = int(sample['NOIS4'])
        
        data['femax'][sampleIndex] = int(sample['FEMAX'])
        data['softw'][sampleIndex] = int(sample['SOFTW'])
        
        data['fe11'][sampleIndex] = int(sample['FE11'])
        data['fe12'][sampleIndex] = int(sample['FE12'])
        data['fe21'][sampleIndex] = int(sample['FE21'])
        data['fe22'][sampleIndex] = int(sample['FE22'])
        
        data['snr1'][sampleIndex] = int(sample['SNR1'])
        data['snr2'][sampleIndex] = int(sample['SNR2'])
        data['snr3'][sampleIndex] = int(sample['SNR3'])
        data['snr4'][sampleIndex] = int(sample['SNR4'])
        
        data['check'][sampleIndex] = int(sample['CHECK'])
        data['jam'][sampleIndex]   = int(sample['JAM'])
        
        for altitude,altitudeIndex in zip(altitudes, range(len(altitudes))):
            echo   = sample[altitude]['CT']
            radial = sample[altitude]['SPEED']
            theta  = sample[altitude]['DIR']
            vertical = sample[altitude]['W']
            
            if radial != INVALID and theta != INVALID:
                theta  = math.pi * float(theta) / 180.0
                radial = float(radial)
                data['u'][sampleIndex][altitudeIndex] = radial * math.sin(theta)
                data['v'][sampleIndex][altitudeIndex] = radial * math.cos(theta)
            
            if echo != INVALID:
                data['echo'][sampleIndex][altitudeIndex] = echo
                
            if vertical != INVALID:
                data['w'][sampleIndex][altitudeIndex] = vertical
    
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
              'units': 'cm s-1',
              },
        'v': {'short_name' : 'v',
              'long_name': 'North/South Component of Wind',
              'standard_name': 'northward_wind',                          
              'units': 'cm s-1',
              },
        'w': {'short_name' : 'w',
              'long_name': 'Vertical Component of Wind',
              'standard_name': 'upward_wind',                          
              'units': 'cm s-1',
              },
        'echo': {'short_name' : 'echo',
                 'long_name': 'Echo Stength',
                 'standard_name': 'echo_strenth',
                 },
        'block' : {'short_name': 'block',
                   'long_name': 'Block Number',
                   'standard_name': 'block_number'
                   },
        'val1': {'short_name' : 'val1',
                 'long_name': 'Number of Beam Validations 1',
                 'standard_name': 'validations_1',
                 },
        'val2': {'short_name' : 'val2',
                 'long_name': 'Number of Beam Validations 2',
                 'standard_name': 'validations_2',
                 },
        'val3': {'short_name' : 'val3',
                 'long_name': 'Number of Beam Validations 3',
                 'standard_name': 'validations_3',
                 },
        'val4': {'short_name' : 'val4',
                 'long_name': 'Number of Beam Validations 4',
                 'standard_name': 'validations_4',
                 },
        'spu1': {'short_name' : 'spu1',
                 'long_name': 'Normalized Probability of False Signal 1',
                 'standard_name': 'probability_1',
                 },
        'spu2': {'short_name' : 'spu2',
                 'long_name': 'Normalized Probability of False Signal 1',
                 'standard_name': 'probability_2',
                 },
        'spu3': {'short_name' : 'spu3',
                 'long_name': 'Normalized Probability of False Signal 3',
                 'standard_name': 'probability_3',
                 },
        'spu4': {'short_name' : 'spu4',
                 'long_name': 'Normalized Probability of False Signal 4',
                 'standard_name': 'probability_4',
                 },
        'nois1': {'short_name' : 'nois1',
                  'long_name': 'Environmental Noise 1',
                  'standard_name': 'ambient_1',
                  'units': 'dB',
              },
        'nois2': {'short_name' : 'nois2',
                  'long_name': 'Environmental Noise 2',
                  'standard_name': 'ambient_2',
                  'units': 'dB',
              },
        'nois3': {'short_name' : 'nois3',
                  'long_name': 'Environmental Noise 3',
                  'standard_name': 'ambient_3',
                  'units': 'dB',
              },
        'nois4': {'short_name' : 'nois4',
                  'long_name': 'Environmental Noise 4',
                  'standard_name': 'ambient_4',
                  'units': 'dB',
              },
        'femax': {'short_name': 'femax',
                  'long_name': 'Maximum Ground Clutter',
                  'standard_name': 'max_clutter',
                  },
        'softw': {'short_name': 'softw',
                        'long_name': 'Software Version',
                        'standard_name': 'software',
                        },
        'fe11': {'short_name': 'fe11',
                 'long_name': 'Number of Frequencies Emitted 11',
                 'standard_name': 'frequencies_11',
                 },
        'fe12': {'short_name': 'fe12',
                 'long_name': 'Number of Frequencies Emitted 12',
                 'standard_name': 'frequencies_12',
                 },
        'fe21': {'short_name': 'fe21',
                 'long_name': 'Number of Frequencies Emitted 21',
                 'standard_name': 'frequencies_21',
                 },
        'fe22': {'short_name': 'fe22',
                 'long_name': 'Number of Frequencies Emitted 22',
                 'standard_name': 'frequencies_22',
                 },
        'snr1': {'short_name' : 'snr1',
                 'long_name': 'Average Signal To Noise Ratio 1',
                 'standard_name': 'signal_to_noise_1',
                 'units': 'dB',
                 },
        'snr2': {'short_name' : 'snr2',
                 'long_name': 'Average Signal To Noise Ratio 2',
                 'standard_name': 'signal_to_noise_2',
                 'units': 'dB',
                 },
        'snr3': {'short_name' : 'snr3',
                 'long_name': 'Average Signal To Noise Ratio 3',
                 'standard_name': 'signal_to_noise_3',
                 'units': 'dB',
                 },
        'snr4': {'short_name' : 'snr4',
                 'long_name': 'Average Signal To Noise Ratio 4',
                 'standard_name': 'signal_to_noise_4',
                 'units': 'dB',
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
        ('echo',  pycdf.NC.FLOAT, ('ntime', 'nz')),
        ('block', pycdf.NC.INT,   ('ntime',)),
        ('val1',  pycdf.NC.INT,   ('ntime',)),
        ('val2',  pycdf.NC.INT,   ('ntime',)),
        ('val3',  pycdf.NC.INT,   ('ntime',)),
        ('val4',  pycdf.NC.INT,   ('ntime',)),
        ('spu1',  pycdf.NC.INT,   ('ntime',)),
        ('spu2',  pycdf.NC.INT,   ('ntime',)),
        ('spu3',  pycdf.NC.INT,   ('ntime',)),
        ('spu4',  pycdf.NC.INT,   ('ntime',)),
        ('nois1', pycdf.NC.INT,   ('ntime',)),
        ('nois2', pycdf.NC.INT,   ('ntime',)),
        ('nois3', pycdf.NC.INT,   ('ntime',)),
        ('nois4', pycdf.NC.INT,   ('ntime',)),
        ('femax', pycdf.NC.INT,   ('ntime',)),
        ('softw', pycdf.NC.INT,   ('ntime',)),
        ('fe11',  pycdf.NC.INT,   ('ntime',)),
        ('fe12',  pycdf.NC.INT,   ('ntime',)),
        ('fe21',  pycdf.NC.INT,   ('ntime',)),
        ('fe22',  pycdf.NC.INT,   ('ntime',)),
        ('snr1',  pycdf.NC.INT,   ('ntime',)),
        ('snr2',  pycdf.NC.INT,   ('ntime',)),
        ('snr3',  pycdf.NC.INT,   ('ntime',)),
        ('snr4',  pycdf.NC.INT,   ('ntime',)),
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
        ('echo',  data['echo'][i]),
        ('block', data['block'][i]),
        ('val1',  data['val1'][i]),
        ('val2',  data['val1'][i]),
        ('val3',  data['val1'][i]),
        ('val4',  data['val1'][i]),
        ('spu1',  data['spu1'][i]),
        ('spu2',  data['spu2'][i]),
        ('spu3',  data['spu3'][i]),
        ('spu4',  data['spu4'][i]),
        ('nois1', data['nois1'][i]),
        ('nois2', data['nois2'][i]),
        ('nois3', data['nois3'][i]),
        ('nois4', data['nois4'][i]),
        ('femax', data['femax'][i]),
        ('softw', data['softw'][i]),
        ('fe11',  data['fe11'][i]),
        ('fe12',  data['fe12'][i]),
        ('fe21',  data['fe21'][i]),
        ('fe22',  data['fe22'][i]),
        ('snr1',  data['snr1'][i]),
        ('snr2',  data['snr2'][i]),
        ('snr3',  data['snr3'][i]),
        ('snr4',  data['snr4'][i]),
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
        ('echo',  data['echo'][i]),
        ('block', data['block'][i]),
        ('val1',  data['val1'][i]),
        ('val2',  data['val1'][i]),
        ('val3',  data['val1'][i]),
        ('val4',  data['val1'][i]),
        ('spu1',  data['spu1'][i]),
        ('spu2',  data['spu2'][i]),
        ('spu3',  data['spu3'][i]),
        ('spu4',  data['spu4'][i]),
        ('nois1', data['nois1'][i]),
        ('nois2', data['nois2'][i]),
        ('nois3', data['nois3'][i]),
        ('nois4', data['nois4'][i]),
        ('femax', data['femax'][i]),
        ('softw', data['softw'][i]),
        ('fe11',  data['fe11'][i]),
        ('fe12',  data['fe12'][i]),
        ('fe21',  data['fe21'][i]),
        ('fe22',  data['fe22'][i]),
        ('snr1',  data['snr1'][i]),
        ('snr2',  data['snr2'][i]),
        ('snr3',  data['snr3'][i]),
        ('snr4',  data['snr4'][i]),
        )

    return (global_atts, var_atts, var_data)
