#!/usr/bin/env python
# Last modified:  Time-stamp: <2014-08-27 16:57:47 haines>
"""
how to parse data, and assert what data and info goes into
creating and updating monthly netcdf files

parse data met data collected on Campbell Scientific DataLogger (loggernet) (csi)

parser : sample date and time, 

creator : lat, lon, z, time, 
updator : time, 


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
    Example met data

    "TOA5","CR1000_B1","CR1000","37541","CR1000.Std.21","CPU:NCWIND_12_Buoy_All.CR1","58723","AMet_6Min"
    "TIMESTAMP","RECORD","Baro_mbar_Avg","RHumidity_Avg","RHumidity_Std","AirTempC_Avg","AirTempC_Std","Rain","Psp_Avg","Psp_Std","Pir_Wm2_Avg","Pir_Wm2_Std"
    "TS","RN","","","","","","","","","",""
    "","","Avg","Avg","Std","Avg","Std","Smp","Avg","Std","Avg","Std"
    "2011-11-01 00:00:59",4590,14.3792,75.59,0.579,15.67,0.05,-22.35,1197.037,45.58967,371.5126,0.9030571
    "2011-11-01 00:06:59",4591,14.37995,74.96,0.912,16.61,0.048,-21,-1071.813,129.5147,381.2539,0.2076943
    "2011-11-01 00:12:59",4592,14.3792,72.71,2.677,17.29,0.032,-15.58,-2056.658,0,381.1828,0.1402813
    "2011-11-01 00:18:59",4593,14.3791,72.63,0.928,17.67,0.041,-19.64,-1895.86,9.866026,381.0333,0.2442325
    
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
        'air_press' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'rh' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'rh_std' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'air_temp' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'air_temp_std' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'rain' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'psp' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'psp_std' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'pir' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'pir_std' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
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
        
        if len(csi)==11:
            # 
            # data['samplenum'][i] = csi[0] # sample number assigned by datalogger in table
            data['air_press'][i] =  csi[1] # Campbell Sci (Viasala) CS106 barometer (mbar)
            # Before Jan 2012, Heise Barometer (psi) to mbar
            data['rh'][i] = csi[2] # relative humidity avg (60 samples for 1 min)
            data['rh_std'][i] = csi[3] # relative humidity std
            data['air_temp'][i] = csi[4] # air temperature avg (deg C)
            data['air_temp_std'][i] = csi[5] # air temperature std (deg C)
            data['rain'][i] = csi[6] # precip gauge cummulative (mm) 
            data['psp'][i] = csi[7] # PSP avg 
            data['psp_std'][i] = csi[8] # PSP std
            data['pir'][i] = csi[9] # PIR avg (W m-2)
            data['pir_std'][i] = csi[10] # PIR std (W m-2)
            i=i+1
        else:
            print ' ... skipping line %d -- %s ' % (i,line)
            continue

        # if re.search
    # for line

    # Specific to buoys using CR1000 in Fall of 2011
    # prior to Jan 01, 2012, pressure sensor was a Heise with units psi
    # afterwards, Campbell Sci CS106 in units mbar,
    # also handle b1/b2 PSP data for each buoy
    if data['dt'][0] < datetime(2012, 1, 1):
        data['air_press'] = udconvert(data['air_press'], 'psi', 'mbar')[0]
        data['rain'] = data['rain']/100 # precip gauge cummulative (mm)
                    
        # specific to buoy B1 and B2
        if platform_info['id'] == 'b1':
            data['psp'] = -1*data['psp']/1000
            data['psp_std'] = -1*data['psp_std']/1000
        if platform_info['id'] == 'b2':
            data['psp'] = numpy.nan*data['psp']
            data['psp_std'] = numpy.nan*data['psp_std']
    
    # some QC
    # good = -40<at & at<60 # does not work
    # good = (-40<at) & (at<60) # THIS WORKS!
    good = (-40<data['air_temp']) & (data['air_temp']<60)
    bad = ~good
    data['air_temp'][bad] = numpy.nan 
    data['air_temp_std'][bad] = numpy.nan 

    # good = (-10<data['rain']) & (data['rain']<60)
    # bad = ~good
    # data['rain'][bad] = numpy.nan 

    # good = (-10<data['rh']) & (data['rh']<120)
    # bad = ~good
    # data['rh'][bad] = numpy.nan 
    # data['rh_std'][bad] = numpy.nan

    # good = (-10<data['psp']) & (data['psp']<1200)
    # bad = ~good
    # data['psp'][bad] = numpy.nan 
    # data['psp_std'][bad] = numpy.nan
    
    # good = (-10<data['pir']) & (data['pir']<1200)
    # bad = ~good
    # data['pir'][bad] = numpy.nan 
    # data['pir_std'][bad] = numpy.nan

    # return the -99999 back into Nan's
    for vn in ['air_temp', 'air_temp_std', 'rain', 'rh', 'rh_std', 'psp', 'psp_std', 'pir', 'pir_std']:
        bad = data[vn]==-99999
        data[vn][bad] = numpy.nan 

    # check that each value in data['dt'] is type datetime, 
    # keep only data that has a resolved datetime
    keep = numpy.array([type(datetime(1970,1,1)) == type(dt) for dt in data['dt'][:]])
    if keep.any():
        for param in data.keys():
            data[param] = data[param][keep]

    return data
 

def creator(platform_info, sensor_info, data):
    #
    # 
    # subset data only to month being processed (see raw2proc.process())
    i = data['in']

    title_str = sensor_info['description']+' at '+ platform_info['location']
    global_atts = {
        'title' : title_str,
        'institution' : platform_info['institution'],
        'institution_url' : platform_info['institution_url'],
        'institution_dods_url' : platform_info['institution_dods_url'],
        'metadata_url' : platform_info['metadata_url'],
        'references' : platform_info['references'],
        'contact' : platform_info['contact'],
        # 
        'source' : platform_info['source']+' '+sensor_info['source'],
        'history' : 'raw2proc using ' + sensor_info['process_module'],
        'comment' : 'File created using pycdf'+pycdfVersion()+' and numpy '+pycdfArrayPkg(),
        # conventions
        'Conventions' : platform_info['conventions'],
        # SEACOOS CDL codes
        'format_category_code' : platform_info['format_category_code'],
        'institution_code' : platform_info['institution_code'],
        'platform_code' : platform_info['id'],
        'package_code' : sensor_info['id'],
        # institution specific
        'project' : platform_info['project'],
        'project_url' : platform_info['project_url'],
        # timeframe of data contained in file yyyy-mm-dd HH:MM:SS
        # first date in monthly file
        'start_date' : data['dt'][i][0].strftime("%Y-%m-%d %H:%M:%S"),
        # last date in monthly file
        'end_date' : data['dt'][i][-1].strftime("%Y-%m-%d %H:%M:%S"), 
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
        'air_press': {'short_name': 'air_press',
                  'long_name': 'Air Pressure',
                  'standard_name': 'air_pressure',                          
                  'units': 'mbar',
                  'z': sensor_info['barometer_height'],
                  'z_units' : 'meter',
                  },
        'air_temp': {'short_name': 'air_temp',
                  'long_name': 'Air Temperature',
                  'standard_name': 'air_temperature',                          
                  'units': 'degC',
                  'z': sensor_info['temperature_height'],
                  'z_units' : 'meter',
                  },
        'air_temp_std': {'short_name': 'air_temp_std',
                  'long_name': 'Standard Deviation of Air Temperature',
                  'standard_name': 'air_temperature',                          
                  'units': 'degC',
                  },
        'rh': {'short_name': 'rh',
                  'long_name': 'Relative Humidity',
                  'standard_name': 'relative_humidity',                          
                  'units': '%',
                  'z': sensor_info['temperature_height'],
                  'z_units' : 'meter',
                  },
        'rh_std': {'short_name': 'rh_std',
                  'long_name': 'Standard Deviation of Relative Humidity',
                  'standard_name': 'relative_humidity',                          
                  'units': '%',
                  },
        'rain': {'short_name': 'rain',
                 'long_name': '6-Minute Rain',
                 'standard_name': 'rain',                          
                 'units': 'inches',
                  },
        'psp': {'short_name': 'psp',
                  'long_name': 'Short-wave Radiation',
                  'standard_name': 'downwelling_shortwave_irradiance',                          
                  'units': 'W m-2',
                  },
        'psp_std': {'short_name': 'psp_std',
                  'long_name': 'Standard Deviation of Short-wave Radiation',
                  'standard_name': 'shortwave_radiation',                          
                  'units': 'W m-2',
                  },
        'pir': {'short_name': 'pir',
                  'long_name': 'Long-wave Radiation',
                  'standard_name': 'longwave_radiation',                          
                  'units': 'W m-2',
                  },
        'pir_std': {'short_name': 'pir_std',
                  'long_name': 'Standard Deviation of Long-wave Radiation',
                  'standard_name': 'longwave_radiation',                          
                  'units': 'W m-2',
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
        ('air_press', NC.FLOAT, ('ntime',)),
        ('rh', NC.FLOAT, ('ntime',)),
        ('rh_std', NC.FLOAT, ('ntime',)),
        ('air_temp', NC.FLOAT, ('ntime',)),
        ('air_temp_std', NC.FLOAT, ('ntime',)),
        ('rain', NC.FLOAT, ('ntime',)),
        ('psp', NC.FLOAT, ('ntime',)),
        ('psp_std', NC.FLOAT, ('ntime',)),
        ('pir', NC.FLOAT, ('ntime',)),
        ('pir_std', NC.FLOAT, ('ntime',)),
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
        ('air_press', data['air_press'][i]),
        ('rh', data['rh'][i]),
        ('rh_std', data['rh_std'][i]),
        ('air_temp', data['air_temp'][i]),
        ('air_temp_std', data['air_temp_std'][i]),
        ('rain', data['rain'][i]),
        ('psp', data['psp'][i]),
        ('psp_std', data['psp_std'][i]),
        ('pir', data['pir'][i]),
        ('pir_std', data['pir_std'][i]),
        )

    return (global_atts, var_atts, dim_inits, var_inits, var_data)

def updater(platform_info, sensor_info, data):
    #
    # subset data only to month being processed (see raw2proc.process())
    i = data['in']

    global_atts = { 
        # update times of data contained in file (yyyy-mm-dd HH:MM:SS)
        # last date in monthly file
        'end_date' : data['dt'][i][-1].strftime("%Y-%m-%d %H:%M:%S"), 
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
    
    # data 
    var_data = (
        ('time', data['time'][i]),
        #
        ('air_press', data['air_press'][i]),
        ('rh', data['rh'][i]),
        ('rh_std', data['rh_std'][i]),
        ('air_temp', data['air_temp'][i]),
        ('air_temp_std', data['air_temp_std'][i]),
        ('rain', data['rain'][i]),
        ('psp', data['psp'][i]),
        ('psp_std', data['psp_std'][i]),
        ('pir', data['pir'][i]),
        ('pir_std', data['pir_std'][i]),
        )

    return (global_atts, var_atts, var_data)
#
