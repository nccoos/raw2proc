#!/usr/bin/env python
# Last modified:  Time-stamp: <2014-02-06 06:44:22 haines>
"""
how to parse data, and assert what data and info goes into
creating and updating monthly netcdf files

parse system data collected on Campbell Scientific DataLogger (loggernet) (csi)

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
    Example system data

    "TOA5","CR1000_B2","CR1000","31722","CR1000.Std.26","CPU:UNC CHill_20_Buoy2_Revision2013_str.CR1","36098","Sys_1Hr"
    "TIMESTAMP","RECORD","P_Batt_Min","P_Batt_TMn","P_Batt_Max","P_Batt_TMx","P_Temp_Avg","P_RH_Avg"
    "TS","RN","","","","","",""
    "","","Min","TMn","Max","TMx","Avg","Avg"
    "2014-02-01 00:00:00",75,13,"2014-01-31 23:50:00",13.22,"2014-01-31 23:01:00",12.82,7.771
    "2014-02-01 01:00:00",76,13.05,"2014-02-01 00:56:00",13.09,"2014-02-01 00:29:00",10.15,8.22
    "2014-02-01 02:00:00",77,13.03,"2014-02-01 01:44:00",13.07,"2014-02-01 01:05:00",7.792,8.64
    "2014-02-01 03:00:00",78,12.95,"2014-02-01 02:01:00",13.04,"2014-02-01 02:04:00",6.323,9.01
    "2014-02-01 04:00:00",79,12.99,"2014-02-01 03:50:00",13.03,"2014-02-01 03:13:00",5.068,9.27

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
        'batt_min' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'batt_max' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'can_temp' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'can_rh' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
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
        
        if len(csi)==7:
            # 
            # data['samplenum'][i] = csi[0] # sample number assigned by datalogger in table
            data['batt_min'][i] =  csi[1] # (v) CR1000 batt min in last hour
            data['batt_max'][i] = csi[3] # (v)
            data['can_temp'][i] = csi[5] # canister temperature avg (deg C) 
            data['can_rh'][i] = csi[6] # canister relative humidity as leak detect (%)
            i=i+1
        else:
            print ' ... skipping line %d -- %s ' % (i,line)
            continue

        # if re.search
    # for line

    # Specific to buoys using CR1000 in Fall of 2011
    # prior to Jan 01, 2012, no difference
    if data['dt'][0] < datetime(2012, 1, 1):
        pass
    
    # some QC
    # good = -40<at & at<60 # does not work
    # good = (-40<at) & (at<60) # THIS WORKS!

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
        'batt_min': {'short_name': 'batt_min',
                  'long_name': 'System Minimum Battery',
                  'standard_name': 'battery minimum',                          
                  'units': 'volt',
                  'z': sensor_info['canister_height'],
                  'z_units' : 'meter',
                  },
        'batt_max': {'short_name': 'batt_max',
                  'long_name': 'System Maximum Battery',
                  'standard_name': 'battery maximum',                          
                  'units': 'volt',
                  'z': sensor_info['canister_height'],
                  'z_units' : 'meter',
                  },
        'can_temp': {'short_name': 'can_temp',
                  'long_name': 'Internal Canister Temperature',
                  'standard_name': 'temperature',                          
                  'units': 'degC',
                  'z': sensor_info['canister_height'],
                  'z_units' : 'meter',
                  },
        'can_rh': {'short_name': 'can_rh',
                  'long_name': 'Internal Canister RH -- Leak Detect',
                  'standard_name': 'relative_humidity',                          
                  'units': '%',
                  'z': sensor_info['canister_height'],
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
        ('batt_min', NC.FLOAT, ('ntime',)),
        ('batt_max', NC.FLOAT, ('ntime',)),
        ('can_temp', NC.FLOAT, ('ntime',)),
        ('can_rh', NC.FLOAT, ('ntime',)),
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
        ('batt_min', data['batt_min'][i]),
        ('batt_max', data['batt_max'][i]),
        ('can_temp', data['can_temp'][i]),
        ('can_rh', data['can_rh'][i]),
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
        ('batt_min', data['batt_min'][i]),
        ('batt_max', data['batt_max'][i]),
        ('can_temp', data['can_temp'][i]),
        ('can_rh', data['can_rh'][i]),
        )

    return (global_atts, var_atts, var_data)
#
