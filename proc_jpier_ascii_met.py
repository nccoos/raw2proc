#!/usr/bin/env python
# Last modified:  Time-stamp: <2011-11-22 13:54:28 haines>
"""
how to parse data, and assert what data and info goes into
creating and updating monthly netcdf files

Texas Weather Instruments - Weather Processing System (WPS) met data
	delimited ASCII file like:
	year mon day hhmm	epoch  tmean hmean wsmean wdmean barom   dewPt wchill rrmean rday rmonth rterm

parser : output delimited ASCII file from onsite perl script
creator : lat, lon, time, air_temp, humidity, wspd, wdir, air_pressure,
		  dew_temp, wchill, rainfall_rate, rainfall_day, rainfall_month, rainfall_term 
updater : time, air_temp, humidity, wspd, wdir, air_pressure,
		  dew_temp, wchill, rainfall_rate, rainfall_day, rainfall_month, rainfall_term

Examples
--------

>> (parse, create, update) = load_processors('proc_jpier_ascii_met')
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
	parse and assign met data from JPIER TWS WPS text file

	"""
 
	i = 0

	# drop header row from incoming lines list
	if lines[0].startswith('year',0,5):
		# print "... Header row present, skipping ..."
		del lines[0]
        
         
        # sort file by fields 0-5
        lines.sort()
            
    
	for line in lines:
		# split line and parse float and integers
		tws = []
		# data row looks like:
		# 2008  1  1 0000 1199163600  17.2  84.8   0.00	0  1015.10  14.4  17.2 1729.1	0.0	0.0 1031.5
       
 		sw = re.split('\s+', line)
		for s in sw:
			m = re.search(REAL_RE_STR, s)
			if m:
				tws.append(float(m.groups()[0]))
		# assign specific fields
		n = len(tws)

		# get sample datetime in UTC from data
		# use epoch tws[4] to get time in UTC
		sample_str = '%04d-%02d-%02d %02d:%02d:00' % tuple(time.gmtime(float(tws[4]))[0:5])
		sample_dt = scanf_datetime(sample_str, fmt='%Y-%m-%d %H:%M:%S')

		air_temp = tws[5]	   # Air Temperature (deg F)
		humidity = tws[6]		# Humidity (%)
		dew_temp = tws[10]	 # Dew Point (deg F)	
		air_pressure = tws[9]   # Air Pressure (Tmean, sec)
		wspd = tws[7]	 # Mean Wind Speed (knots)
		wdir = tws[8]	   # Mean Wind Direction (deg from N)
		wchill = tws[11]	# Wind Chill (deg F)
		rainfall_rate = tws[12]  # Rainfall Rate ()
		rainfall_day = tws[13]   # Rainfall amount last 24 hours (in)
		rainfall_month = tws[14] # Rainfall amount last month (in)
		rainfall_term = tws[15]  # Rainfall amount since installation (in)

		# set up dict of data if first line
		if i==0:
			data = {
				'dt' : numpy.array(numpy.ones((len(lines),), dtype=object)*numpy.nan),
				'time' : numpy.array(numpy.ones((len(lines),), dtype=long)*numpy.nan),
				'air_temp' : numpy.array(numpy.ones((len(lines)), dtype=float)*numpy.nan),
				'humidity' : numpy.array(numpy.ones((len(lines)), dtype=float)*numpy.nan),
				'dew_temp' : numpy.array(numpy.ones((len(lines)), dtype=float)*numpy.nan),
				'air_pressure' : numpy.array(numpy.ones((len(lines)), dtype=float)*numpy.nan),
				'wspd' : numpy.array(numpy.ones((len(lines)), dtype=float)*numpy.nan),
				'wdir' : numpy.array(numpy.ones((len(lines)), dtype=float)*numpy.nan),
				'wchill' : numpy.array(numpy.ones((len(lines)), dtype=float)*numpy.nan),
				'rainfall_rate' : numpy.array(numpy.ones((len(lines)), dtype=float)*numpy.nan),
				'rainfall_day' : numpy.array(numpy.ones((len(lines)), dtype=float)*numpy.nan),
				'rainfall_month' : numpy.array(numpy.ones((len(lines)), dtype=float)*numpy.nan),
				'rainfall_term' : numpy.array(numpy.ones((len(lines)), dtype=float)*numpy.nan),
				}
		
		data['dt'][i] = sample_dt # sample datetime
		data['time'][i] = dt2es(sample_dt) # sample time in epoch seconds
		data['air_temp'][i] = air_temp
		data['humidity'][i] = humidity
		data['dew_temp'][i] = dew_temp
		data['air_pressure'][i] =  air_pressure
		data['wspd'][i] =  wspd
		data['wdir'][i] = wdir
		data['wchill'][i] = wchill
		data['rainfall_rate'][i] = rainfall_rate
		data['rainfall_day'][i] =  rainfall_day
		data['rainfall_month'][i] =  rainfall_month
		data['rainfall_term'][i] = rainfall_term 
		i = i+1

	return data

def creator(platform_info, sensor_info, data):
	#
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
		'source' : 'TWS Met station observation',
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
		'start_date' : data['dt'][0].strftime("%Y-%m-%d %H:%M:%S"),
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
		
		'air_temp' :	{'short_name': 'air_temp',
						'long_name': 'Air Temperature',
						'standard_name': 'air_temperature',
						'units': 'degrees_Celsius',
						},
		'humidity' : 	{'short_name': 'humidity',
						'long_name': 'Humidity',
						'standard_name': 'humidity',
						'units': '%',
						},
		'dew_temp' : 	{'short_name': 'dew_temp',
						'long_name': 'Dew Temperature',
						'standard_name': 'dew_temp',						  
						'units': 'degrees_Celsius',
						},
		'air_pressure' : {'short_name': 'air_pressure',
						'long_name': 'Air Pressure at Barometer Height',
						'standard_name': 'air_pressure',						  
						'units': 'hPa',
						},
		'wspd' : 	{'short_name': 'wspd',
						'long_name': 'Wind Speed',
						'standard_name': 'wind_speed',
						'units': 'm s-1',
						'can_be_normalized': 'no',
						},
		'wdir' :	{'short_name': 'wdir',
						'long_name': 'Wind Direction from',
						'standard_name': 'wind_from_direction',
						'reference': 'clockwise from True North',
						'valid_range': '0., 360',
						'units': 'degrees',
						},
		'wchill' : 	{'short_name': 'wchill',
						'long_name': 'Wind Chill',
						'standard_name': 'wind_chill',
						'units': 'degrees_Celsius',
						},
		'rainfall_rate' : 	{'short_name': 'rR',
						'long_name': 'Rainfall Rate',
						'standard_name': 'rainfall_rate',
						'units': 'mm hr-1',
						},
		'rainfall_day' : {'short_name': 'rD',
						'long_name': 'Rainfall Day',
						'standard_name': 'rainfall_day',
						'units': 'mm',
						},
		'rainfall_month' : {'short_name': 'rM',
						'long_name': 'Rainfall Month',
						'standard_name': 'rainfall_month',
						'units': 'mm',
						},
		'rainfall_term' : {'short_name': 'rT',
						'long_name': 'Rainfall Term',
						'standard_name': 'rainfall_term',
						'units': 'mm',
						},
	}

	# dimension names use tuple so order of initialization is maintained
	dim_inits = (
		('ntime', NC.UNLIMITED),
		('nlat', 1),
		('nlon', 1),
		('nz', 1)
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
		('air_temp', NC.FLOAT, ('ntime',)),
		('humidity', NC.FLOAT, ('ntime',)),
		('dew_temp', NC.FLOAT, ('ntime',)),
		('air_pressure', NC.FLOAT, ('ntime',)),
		('wspd', NC.FLOAT, ('ntime',)),
		('wdir', NC.FLOAT, ('ntime',)),
		('wchill', NC.FLOAT, ('ntime',)),
		('rainfall_rate', NC.FLOAT, ('ntime',)),
		('rainfall_day', NC.FLOAT, ('ntime',)),
		('rainfall_month', NC.FLOAT, ('ntime',)),
		('rainfall_term', NC.FLOAT, ('ntime',)),
		)

	# subset data only to month being processed (see raw2proc.process())
	i = data['in']

	# var data 
	var_data = (
		('lat',  platform_info['lat']),
		('lon', platform_info['lon']),
		('z', 6),
		#
		('time', data['time'][i]),
		('air_temp', data['air_temp'][i]),
		('humidity', data['humidity'][i]),
		('dew_temp', data['dew_temp'][i]),
		('air_pressure', data['air_pressure'][i]),
		('wspd', data['wspd'][i]),
		('wdir', data['wdir'][i]),
		('wchill', data['wchill'][i]),
		('rainfall_rate', data['rainfall_rate'][i]),
		('rainfall_day', data['rainfall_day'][i]),
		('rainfall_month', data['rainfall_month'][i]),
		('rainfall_term', data['rainfall_term'][i]),
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
		('air_temp', data['air_temp'][i]),
		('humidity', data['humidity'][i]),
		('dew_temp', data['dew_temp'][i]),
		('air_pressure', data['air_pressure'][i]),
		('wspd', data['wspd'][i]),
		('wdir', data['wdir'][i]),
		('wchill', data['wchill'][i]),
		('rainfall_rate', data['rainfall_rate'][i]),
		('rainfall_day', data['rainfall_day'][i]),
		('rainfall_month', data['rainfall_month'][i]),
		('rainfall_term', data['rainfall_term'][i]),
		)

	return (global_atts, var_atts, var_data)

#
