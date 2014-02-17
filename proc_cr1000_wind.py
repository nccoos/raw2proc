#!/usr/bin/env python
# Last modified:  Time-stamp: <2014-02-17 13:37:43 haines>
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
    Example wind data

    Stats (avg, std, and max) for wind sampled every second for one minute DURING a 6 minute time period.  Stats are NOT over 6 minutes, as
    the time stamp would have you believe.
    
    "TOA5","CR1000_B1","CR1000","37541","CR1000.Std.21","CPU:NCWIND_12_Buoy_All.CR1","58723","AWind_6Min"
    "TIMESTAMP","RECORD","W1_SpeedAvg","W1_DirAvg","W1_SpeedMax","W1_SpeedStd","W2_SpeedAvg","W2_DirAvg","W2_SpeedMax","W2_SpeedStd"
    "TS","RN","","Deg","","","","Deg","",""
    "","","WVc","WVc","Max","Std","WVc","WVc","Max","Std"
    "2011-12-01 00:01:59",6507,8.32,319.1,10.09,0.781,8.15,310.9,10.09,0.832
    "2011-12-01 00:07:59",6508,9.43,323.3,11.27,1.094,9.11,315.8,10.68,1.015
    "2011-12-01 00:13:59",6509,9.94,308.6,12.35,1.077,9.74,301.3,11.96,1.027
    "2011-12-01 00:19:59",6510,8.86,304.5,10.98,1.003,8.8,296.4,11.27,1.066
    "2011-12-01 00:25:59",6511,9.02,310.8,10.98,1.023,8.95,302.4,10.78,0.964
    "2011-12-01 00:31:59",6512,9.58,304.9,11.76,1.156,9.39,296.7,11.76,1.167
    
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
        'wspd1' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'wspd1_std' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'wgust1' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'wdir1' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'wspd2' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'wspd2_std' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'wgust2' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'wdir2' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
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
        
        if len(csi)==9:
            # 
            # data['samplenum'][i] = csi[0] # sample number assigned by datalogger in table
            data['wspd1'][i] = csi[1] # 
            data['wdir1'][i] = csi[2] # 
            data['wgust1'][i] = csi[3] # relative humidity std
            data['wspd1_std'][i] = csi[4] # air temperature avg (deg C)
            data['wspd2'][i] = csi[5] # air temperature std (deg C)
            data['wdir2'][i] = csi[6] # precip gauge cummulative 
            data['wgust2'][i] = csi[7] # PSP avg 
            data['wspd2_std'][i] = csi[8] # PSP std
            i=i+1
        else:
            print ' ... skipping line %d -- %s ' % (i,line)
            continue

        # if re.search
    # for line

    # cannot figure out how to combine the two operations
    # for some reason, this one liner does not work
    bad = data['wdir1']==0    # print ' ... ... Number of zero wdir1 = %d' % numpy.sum(bad)
    data['wdir1'][bad] = numpy.nan
    bad = data['wdir2']==0    # print ' ... ... Number of zero wdir1 = %d' % numpy.sum(bad)
    data['wdir2'][bad] = numpy.nan

    # adjust wind dir in magnetic North to True North by using the station mvar
    data['wdir1'] = numpy.mod(data['wdir1'] + platform_info['mvar'] + 360., 360.)
    data['wdir2'] = numpy.mod(data['wdir2'] + platform_info['mvar'] + 360., 360.)
                                   
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
        'wspd1' : {'short_name': 'wspd',
                  'long_name': 'Wind Speed',
                  'standard_name': 'wind_speed',
                  'units': 'm s-1',
                  'can_be_normalized': 'no',
                  'z' : sensor_info['anemometer1_height'],
                  'z_units' : 'meter',
                  },
        'wdir1' : {'short_name': 'wdir',
                  'long_name': 'Wind Direction from',
                  'standard_name': 'wind_from_direction',
                  'reference': 'clockwise from True North',
                  'valid_range': (0., 360),
                  'units': 'degrees',
                  'z' : sensor_info['anemometer1_height'],
                  'z_units' : 'meter',
                  },
        'wgust1' : {'short_name': 'wgust',
                  'long_name': 'Wind Gust',
                  'standard_name': 'wind_gust',
                  'units': 'm s-1',
                  'can_be_normalized': 'no',
                  'z' : sensor_info['anemometer1_height'],
                  'z_units' : 'meter',
                  },
        'wspd1_std' : {'short_name': 'wspd std',
                  'long_name': 'Standard Deviation of Wind Speed ',
                  'standard_name': 'wind_speed standard_deviation',
                  'units': 'm s-1',
                  'can_be_normalized': 'no',
                  'z' : sensor_info['anemometer1_height'],
                  'z_units' : 'meter',
                  },
        # Second anemometer
        'wspd2' : {'short_name': 'wspd',
                  'long_name': 'Wind Speed',
                  'standard_name': 'wind_speed',
                  'units': 'm s-1',
                  'can_be_normalized': 'no',
                  'z' : sensor_info['anemometer2_height'],
                  'z_units' : 'meter',
                  },
        'wdir2' : {'short_name': 'wdir',
                  'long_name': 'Wind Direction from',
                  'standard_name': 'wind_from_direction',
                  'reference': 'clockwise from True North',
                  'valid_range': (0., 360),
                  'units': 'degrees',
                  'z' : sensor_info['anemometer2_height'],
                  'z_units' : 'meter',
                  },
        'wgust2' : {'short_name': 'wgust',
                  'long_name': 'Wind Gust',
                  'standard_name': 'wind_gust',
                  'units': 'm s-1',
                  'can_be_normalized': 'no',
                  'z' : sensor_info['anemometer2_height'],
                  'z_units' : 'meter',
                  },
        'wspd2_std' : {'short_name': 'wspd std',
                  'long_name': 'Standard Deviation of Wind Speed ',
                  'standard_name': 'wind_speed standard_deviation',
                  'units': 'm s-1',
                  'can_be_normalized': 'no',
                  'z' : sensor_info['anemometer2_height'],
                  'z_units' : 'meter',
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
        ('wspd1', NC.FLOAT, ('ntime',)),
        ('wdir1', NC.FLOAT, ('ntime',)),
        ('wgust1', NC.FLOAT, ('ntime',)),
        ('wspd1_std', NC.FLOAT, ('ntime',)),
        ('wspd2', NC.FLOAT, ('ntime',)),
        ('wdir2', NC.FLOAT, ('ntime',)),
        ('wgust2', NC.FLOAT, ('ntime',)),
        ('wspd2_std', NC.FLOAT, ('ntime',)),
        )

    # var data 
    var_data = (
        ('lat',  platform_info['lat']),
        ('lon', platform_info['lon']),
        ('z', platform_info['altitude']),
        #
        ('time', data['time'][i]),
        #
        ('wspd1', data['wspd1'][i]),
        ('wdir1', data['wdir1'][i]),
        ('wgust1', data['wgust1'][i]),
        ('wspd1_std', data['wspd1_std'][i]),
        ('wspd2', data['wspd2'][i]),
        ('wdir2', data['wdir2'][i]),
        ('wgust2', data['wgust2'][i]),
        ('wspd2_std', data['wspd2_std'][i]),
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
        ('wspd1', data['wspd1'][i]),
        ('wdir1', data['wdir1'][i]),
        ('wgust1', data['wgust1'][i]),
        ('wspd1_std', data['wspd1_std'][i]),
        ('wspd2', data['wspd2'][i]),
        ('wdir2', data['wdir2'][i]),
        ('wgust2', data['wgust2'][i]),
        ('wspd2_std', data['wspd2_std'][i]),
        )

    return (global_atts, var_atts, var_data)
#
