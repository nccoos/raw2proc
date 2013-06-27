#!/usr/bin/env python
# Last modified:  Time-stamp: <2010-12-09 16:15:23 haines>
"""
how to parse data, and assert what data and info goes into
creating and updating monthly netcdf files


parser : output delimited ASCII file from onsite perl script
creator : lat, lon, z, time, wspd, wdir, cdir, u, v, nwnd

updater : time, wspd, wdir, cdir, u, v, nwnd


Examples
--------

>> (parse, create, update) = load_processors('proc_avp_ascii_wnd')
or
>> si = get_config(cn+'.sensor_info')
>> (parse, create, update) = load_processors(si['met']['proc_module'])

>> lines = load_data(filename)
>> data = parse(platform_info, sensor_info, lines)
>> create(platform_info, sensor_info, data) or
>> update(platform_info, sensor_info, data)

"""

from raw2proc import *
from procutil import *
from ncutil import *
import time

now_dt = datetime.utcnow()
now_dt.replace(microsecond=0)

def parser(platform_info, sensor_info, lines):
    """
    parse Automated Vertical Profile Station (AVP) Wind data 

    Notes
    -----
    1. Wind: 

    Date, time, speed, dir, compass dir, North , East, n-samples
        (m/s) (magN) (magN)      (m/s)   (m/s)

    08/11/2008 00:00:00    5.881  197  197  -5.638  -1.674     696
    08/11/2008 00:30:00    5.506  216  197  -4.448  -3.246     699
    08/11/2008 01:00:00    7.233  329  159   6.183  -3.754     705

    """
    import numpy
    from datetime import datetime
    from time import strptime

    # get sample datetime from filename
    fn = sensor_info['fn']
    sample_dt_start = filt_datetime(fn)

    # if line has weird ascii chars -- remove it
    for index, line in enumerate(lines):
        if re.search(r"[\x1a]", line):
            # print '... ... remove unexpected  ... ' + str(line)
            lines.pop(index)

    lines.sort()
    N = len(lines)
    data = {
        'dt' : numpy.array(numpy.ones((N,), dtype=object)*numpy.nan),
        'time' : numpy.array(numpy.ones((N,), dtype=long)*numpy.nan),
        'wspd' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'wdir' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'cdir' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'v' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'u' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'nwnd' : numpy.array(numpy.ones((N,), dtype=int)*numpy.nan),
        }

    i = 0 
    mvar = platform_info['mvar']  # Magnetic Variation at station

    for line in lines:
        # if line has weird ascii chars -- skip it and iterate to next line
        if re.search(r"[\x1a]", line):
            print 'skipping bad data line ... ' + str(line)
            continue
            
        wnd = []

        # split line and parse float and integers
        sw = re.split('[\s\/\:]*', line)
        for s in sw:
            m = re.search(REAL_RE_STR, s)
            if m:
                wnd.append(float(m.groups()[0]))

        if len(wnd)>=11:
            # get sample datetime from data
            sample_str = '%02d-%02d-%4d %02d:%02d:%02d' % tuple(wnd[0:6])
            if  sensor_info['utc_offset']:
                sample_dt = scanf_datetime(sample_str, fmt='%m-%d-%Y %H:%M:%S') + \
                            timedelta(hours=sensor_info['utc_offset'])
            else:
                sample_dt = scanf_datetime(sample_str, fmt='%m-%d-%Y %H:%M:%S')

            wspd = int(wnd[6]) # wind speed (m/s)
            wdir = int(wnd[7]) # wind dir (mag N)
            cdir = wnd[8]      # compass dir (mag N)
            u = wnd[9]         # Easterly (?) Component (m/s) (mag or true??)
            v = wnd[10]        # Northerly (?) Component (m/s) (mag or true??)
            if len(wnd)>=12:
                nwnd = int(wnd[11])
            else:
                nwnd = numpy.nan # Number of samples in wind average
            # prior to Sep 2008 number of samples were not recorded
            
            # combine wind dir and buoy compass direction
            # correct direction from magnetic N to true N
            # rotate u, v to true N
            # or
            # recompute u, v from direction and speed

            data['dt'][i] = sample_dt # sample datetime
            data['time'][i] = dt2es(sample_dt) # sample time in epoch seconds
            data['wspd'][i] =  wspd
            data['wdir'][i] = wdir
            data['cdir'][i] = cdir
            data['u'][i] = u
            data['v'][i] = v
            data['nwnd'][i] = nwnd

            i=i+1

        # if len(wnd)>=11
    # for line

    return data

def creator(platform_info, sensor_info, data):
	#
	# subset data only to month being processed (see raw2proc.process())
        i = data['in']
        dt = data['dt'][i]
	# 
	title_str = sensor_info['description']+' at '+ platform_info['location']
	global_atts = { 
		'title' : title_str,
		'institution' : 'University of North Carolina at Chapel Hill (UNC-CH)',
		'institution_url' : 'http://nccoos.org',
		'institution_dods_url' : 'http://nccoos.org',
		'metadata_url' : 'http://nccoos.org',
		'references' : 'http://nccoos.org',
		'contact' : 'Sara Haines (haines@email.unc.edu)',
		# 
		'source' : 'AVP Wind Observations',
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
		'project' : 'North Carolina Coastal Ocean Observing System (NCCOOS)',
		'project_url' : 'http://nccoos.org',
		# timeframe of data contained in file yyyy-mm-dd HH:MM:SS
		'start_date' : dt[0].strftime("%Y-%m-%d %H:%M:%S"),
		'end_date' : dt[-1].strftime("%Y-%m-%d %H:%M:%S"), 
		'release_date' : now_dt.strftime("%Y-%m-%d %H:%M:%S"),
		#
		'creation_date' : now_dt.strftime("%Y-%m-%d %H:%M:%S"),
		'modification_date' : now_dt.strftime("%Y-%m-%d %H:%M:%S"),
		'process_level' : 'level1',
		#
		# must type match to data (e.g. fillvalue is real if data is real)
		'_FillValue' : numpy.nan,
		}

	var_atts = {
		# coordinate variables
		'time' : {'short_name': 'time',
			  'long_name': 'Sample Time',
			  'standard_name': 'time',
			  'units': 'seconds since 1970-1-1 00:00:00 -0', # UTC
			  'axis': 'T',
			  },
		'lat' : {'short_name': 'lat',
			 'long_name': 'Latitude in Decimal Degrees',
			 'standard_name': 'latitude',
			 'reference':'geographic coordinates',
			 'units': 'degrees_north',
			 'valid_range':(-90.,90.),
			 'axis': 'Y',
			 },
		'lon' : {'short_name': 'lon',
			 'long_name': 'Longitude in Decimal Degrees',
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
		       'positive': 'up',
		       'units': 'm',
		       'axis': 'Z',
		       },
		# data variables
		'wspd' : {'short_name': 'wspd',
			  'long_name': 'Wind Speed',
			  'standard_name': 'wind_speed',
			  'units': 'm s-1',
			  'can_be_normalized': 'no',
			  'z' : sensor_info['anemometer_height'],
			  },
		'wdir' : {'short_name': 'wdir',
			  'long_name': 'Wind Direction from',
			  'standard_name': 'wind_from_direction',
			  'reference': 'clockwise from Magnetic North',
			  'valid_range': (0., 360),
			  'units': 'degrees',
			  'z' : sensor_info['anemometer_height'],
			  },
		'cdir' :  {'short_name': 'cdir',
			   'long_name': 'Buoy Orientation',
			   'standard_name': 'compass_direction',
			   'reference': 'clockwise from Magnetic North',
			   'valid_range': (0., 360),
			   'units': 'degrees',
			   },
		'u' : {'short_name': 'u',
		       'long_name': 'East/West Component of Wind',
		       'standard_name': 'eastward_wind',
		       'reference': 'relative to True East (?)',
		       'units': 'm s-1',
		       'can_be_normalized': 'no',
		       'z' : sensor_info['anemometer_height'],
		       },
		'v' : {'short_name': 'v',
		       'long_name': 'North/South Component of Wind',
		       'standard_name': 'northward_wind',
		       'reference': 'relative to True North (?)',
		       'units': 'm s-1',
		       'can_be_normalized': 'no',
		       'z' : sensor_info['anemometer_height'],
		       },
		'nwnd' : {'short_name': 'nwnd',
		       'long_name': 'Number of wind samples in sample period',
		       'standard_name': 'number_of_samples',
		       'units': '',
		       },
		
	}
	
	# dimension names use tuple so order of initialization is maintained
	dim_inits = (
		('time', NC.UNLIMITED),
		('lat', 1),
		('lon', 1),
		('z', 1)
		)

	# using tuple of tuples so order of initialization is maintained
	# using dict for attributes order of init not important
	# use dimension names not values
	# (varName, varType, (dimName1, [dimName2], ...))
	var_inits = (
		# coordinate variables
		('time', NC.INT, ('time',)),
		('lat', NC.FLOAT, ('lat',)),
		('lon', NC.FLOAT, ('lon',)),
		('z',  NC.FLOAT, ('z',)),
		# data variables
		('wspd', NC.FLOAT, ('time',)),
		('wdir', NC.FLOAT, ('time',)),
		('cdir', NC.FLOAT, ('time',)),
		('u', NC.FLOAT, ('time',)),
		('v', NC.FLOAT, ('time',)),
		('nwnd', NC.FLOAT, ('time',)),
		)

	# var data 
	var_data = (
		('lat',  platform_info['lat']),
		('lon', platform_info['lon']),
		('z', sensor_info['anemometer_height']),
		#
		('time', data['time'][i]),
		('wspd', data['wspd'][i]),
		('wdir', data['wdir'][i]),
		('cdir', data['cdir'][i]),
		('u', data['u'][i]),
		('v', data['v'][i]),
		('nwnd', data['nwnd'][i]),
		)
		
	return (global_atts, var_atts, dim_inits, var_inits, var_data)

def updater(platform_info, sensor_info, data):
	#
	# subset data only to month being processed (see raw2proc.process())
        i = data['in']
        dt = data['dt'][i]
        #
	global_atts = { 
		# update times of data contained in file (yyyy-mm-dd HH:MM:SS)
		# last date in monthly file
		'end_date' : dt[-1].strftime("%Y-%m-%d %H:%M:%S"), 
		'release_date' : now_dt.strftime("%Y-%m-%d %H:%M:%S"),
		#
		'modification_date' : now_dt.strftime("%Y-%m-%d %H:%M:%S"),
		}

	# data variables
	# update any variable attributes like range, min, max
	var_atts = {}
	# var_atts = {
	#	'u': {'max': max(data.u),
	#		  'min': min(data.v),
	#		  },
	#	'v': {'max': max(data.u),
	#		  'min': min(data.v),
	#		  },
	#	}
	
	# subset data only to month being processed (see raw2proc.process())
	i = data['in']

	# data 
	var_data = (
		('time', data['time'][i]),
		('wspd', data['wspd'][i]),
		('wdir', data['wdir'][i]),
		('cdir', data['cdir'][i]),
		('u', data['u'][i]),
		('v', data['v'][i]),
		('nwnd', data['nwnd'][i]),
		)

	return (global_atts, var_atts, var_data)

#
