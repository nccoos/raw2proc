#!/usr/bin/env python
# Last modified:  Time-stamp: <2014-02-04 15:05:55 haines>
"""
how to parse data, and assert what data and info goes into
creating and updating monthly netcdf files

parse data compass data collected on Campbell Scientific DataLogger (loggernet) (csi)

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
    Example compass data

    "TOA5","CR1000_B2","CR1000","31722","CR1000.Std.26","CPU:UNC CHill_20_Buoy2_Revision2013_str.CR1","36098","Comp_6Min"
    "TIMESTAMP","RECORD","Heading_Avg","Heading_Std","PITCH_Avg","PITCH_Std","PITCH_Max","ROLL_Avg","ROLL_Std","ROLL_Max"
    "TS","RN","","Deg","","","","","",""
    "","","WVc","WVc","Avg","Std","Max","Avg","Std","Max"
    "2014-02-01 00:00:59",593,14.37,0.242,1.01,0.03,1.1,0.227,0.051,0.4
    "2014-02-01 00:06:59",594,14.32,0.258,1.01,0.03,1.1,0.227,0.044,0.3
    "2014-02-01 00:12:59",595,14.22,0.088,1.017,0.037,1.1,0.217,0.037,0.3
    "2014-02-01 00:24:59",596,14.24,0.095,1,0.018,1.1,0.232,0.047,0.3
    "2014-02-01 00:30:59",597,14.18,0.108,1.007,0.025,1.1,0.223,0.042,0.3
    
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
        'hdg' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'hdg_std' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'pitch' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'pitch_std' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'pitch_max' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'roll' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'roll_std' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'roll_max' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
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
            data['hdg'][i] =  csi[1] # Honeywell compass Heading avg (deg Mag North) (60 samples for 1 min) 
            data['hdg_std'][i] = csi[2] # heading std (deg)
            data['pitch'][i] = csi[3] # 1 min avg of pitch (deg)
            data['pitch_std'][i] = csi[4] # pitch std (deg )
            data['pitch_max'][i] = csi[5] # pitch angle max (deg)
            data['roll'][i] = csi[6] # avg roll (deg) 
            data['roll_std'][i] = csi[7] # roll std (deg) 
            data['roll_max'][i] = csi[8] # roll max (deg)
            i=i+1
        else:
            print ' ... skipping line %d -- %s ' % (i,line)
            continue

        # if re.search
    # for line

    # Specific to buoys using CR1000 in Fall of 2011
    # prior to Jan 01, 2012, nothing different in compass
    # but can be handled here if there was difference
    if data['dt'][0] < datetime(2012, 1, 1):
        pass
    
    # some QC
    # good = -40<at & at<60 # does not work
    # good = (-40<at) & (at<60) # THIS WORKS!
    # good = (0<data['hdg']) & (data['hdg']<360)
    # bad = ~good
    # data['hdg'][bad] = numpy.nan 
    # data['hdg_std'][bad] = numpy.nan 

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
        'hdg': {'short_name': 'hdg',
                  'long_name': 'Heading',
                  'standard_name': 'heading',                          
                  'units': 'degrees',
                  'reference': 'clockwise from Magnetic North',
                  'z': sensor_info['compass_height'],
                  'z_units' : 'meter',
                  },
        'hdg_std': {'short_name': 'hdg_std',
                  'long_name': 'Standard Deviation of Heading',
                  'standard_name': 'heading standard_deviation',                          
                  'units': 'degrees',
                  'z': sensor_info['compass_height'],
                  'z_units' : 'meter',
                  },
        'pitch': {'short_name': 'pitch',
                  'long_name': 'Pitch',
                  'standard_name': 'pitch',                          
                  'units': 'degrees',
                  },
        'pitch_std': {'short_name': 'pitch_std',
                  'long_name': 'Standard Deviation of Pitch',
                  'standard_name': 'pitch standard_deviation',                          
                  'units': 'degrees',
                  'z': sensor_info['compass_height'],
                  'z_units' : 'meter',
                  },
        'pitch_max': {'short_name': 'pitch_max',
                  'long_name': 'Maximum of Pitch',
                  'standard_name': 'pitch maximum',                          
                  'units': 'degrees',
                  'z': sensor_info['compass_height'],
                  'z_units' : 'meter',
                  },
        'roll': {'short_name': 'roll',
                  'long_name': 'Roll',
                  'standard_name': 'roll',                          
                  'units': 'degrees',
                  },
        'roll_std': {'short_name': 'roll_std',
                  'long_name': 'Standard Deviation of Roll',
                  'standard_name': 'roll standard_deviation',                          
                  'units': 'degrees',
                  'z': sensor_info['compass_height'],
                  'z_units' : 'meter',
                  },
        'roll_max': {'short_name': 'roll_max',
                  'long_name': 'Maximum of Roll',
                  'standard_name': 'roll maximum',                          
                  'units': 'degrees',
                  'z': sensor_info['compass_height'],
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
        ('hdg', NC.FLOAT, ('ntime',)),
        ('hdg_std', NC.FLOAT, ('ntime',)),
        ('pitch', NC.FLOAT, ('ntime',)),
        ('pitch_std', NC.FLOAT, ('ntime',)),
        ('pitch_max', NC.FLOAT, ('ntime',)),
        ('roll', NC.FLOAT, ('ntime',)),
        ('roll_std', NC.FLOAT, ('ntime',)),
        ('roll_max', NC.FLOAT, ('ntime',)),
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
        ('hdg', data['hdg'][i]),
        ('hdg_std', data['hdg_std'][i]),
        ('pitch', data['pitch'][i]),
        ('pitch_std', data['pitch_std'][i]),
        ('pitch_max', data['pitch_max'][i]),
        ('roll', data['roll'][i]),
        ('roll_std', data['roll_std'][i]),
        ('roll_max', data['roll_max'][i]),
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
        ('hdg', data['hdg'][i]),
        ('hdg_std', data['hdg_std'][i]),
        ('pitch', data['pitch'][i]),
        ('pitch_std', data['pitch_std'][i]),
        ('pitch_max', data['pitch_max'][i]),
        ('roll', data['roll'][i]),
        ('roll_std', data['roll_std'][i]),
        ('roll_max', data['roll_max'][i]),
        )

    return (global_atts, var_atts, var_data)
#
