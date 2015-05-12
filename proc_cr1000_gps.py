#!/usr/bin/env python
# Last modified:  Time-stamp: <2014-08-27 17:22:15 haines>
"""
how to parse data, and assert what data and info goes into
creating and updating monthly netcdf files

parse gps data collected on Campbell Scientific DataLogger (loggernet) (csi)

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
    Example gps data

    "TOA5","CR1000_B1","CR1000","55356","CR1000.Std.25","CPU:UNC CHill_20_Buoy1_Revision2013.CR1","59421","GPS_1Hr"
    "TIMESTAMP","RECORD","GPSParseStr(1)","GPSParseStr(2)","GPSParseStr(3)","GPSParseStr(4)","GPSParseStr(5)","GPSParseStr(6)","GPSParseStr(7)","GPSParseStr(8)","GPSParseStr(9)","GPSParseStr(10)","GPSParseStr(11)","GPSParseStr(12)"
    "TS","RN","","","","","","","","","","","",""
    "","","Smp","Smp","Smp","Smp","Smp","Smp","Smp","Smp","Smp","Smp","Smp","Smp"
    "2014-02-01 00:52:01",77,"$GPRMC","005155","A","3443.3939","N","07645.1690","W","000.0","000.0","010214","010.0","W"
    "2014-02-01 01:52:01",78,"$GPRMC","015155","A","3443.3926","N","07645.1688","W","000.0","000.0","010214","010.0","W"
    "2014-02-01 02:52:01",79,"$GPRMC","025155","A","3443.3927","N","07645.1686","W","000.2","000.0","010214","010.0","W"
    "2014-02-01 03:52:01",80,"$GPRMC","035155","A","3443.3931","N","07645.1685","W","000.0","000.0","010214","010.0","W"
    "2014-02-01 04:52:01",81,"$GPRMC","045155","A","3443.3943","N","07645.1687","W","000.0","000.0","010214","010.0","W"
    "2014-02-01 05:52:01",82,"$GPRMC","055155","A","3443.3934","N","07645.1695","W","000.0","000.0","010214","010.0","W"
    "2014-02-01 06:52:01",83,"$GPRMC","065155","A","3443.3930","N","07645.1680","W","000.0","000.0","010214","010.0","W"
    
    RMC - NMEA has its own version of essential gps pvt (position, velocity, time) data. It is called RMC, The Recommended Minimum, which will look similar to:

    $GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A
    
    Where:
    RMC          Recommended Minimum sentence C
    123519       Fix taken at 12:35:19 UTC
    A            Status A=active or V=Void.
    4807.038,N   Latitude 48 deg 07.038' N
    01131.000,E  Longitude 11 deg 31.000' E
    022.4        Speed over the ground in knots
    084.4        Track angle in degrees True
    230394       Date - 23rd of March 1994
    003.1,W      Magnetic Variation
    *6A          The checksum data, always begins with *
                                                      
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
        'gps_dt' : numpy.array(numpy.ones((N,), dtype=object)*numpy.nan), # gps fix datetime object    
        'gps_time' : numpy.array(numpy.ones((N,), dtype=long)*numpy.nan), # gps fix time (epoch secs)  
        'gps_active' : numpy.array(numpy.ones((N,), dtype=int)*numpy.nan),       # quality of fix (1 == Active, 0 == Void)
        'gps_lat' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),     # lat of fix                 
        'gps_lon' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),     # lon of fix                 
        'gps_mvar' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),    # magnetic variation at fix  
        'gps_sog' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),     # speed over ground (kts)         
        'gps_cog' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),     # course over ground or track deg True
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
        # for s in sw[1:]:
        #     m = re.search(REAL_RE_STR, s)
        #     if m:
        #         csi.append(float(m.groups()[0]))

        if  sensor_info['utc_offset']:
            sample_dt = scanf_datetime(sw[0], fmt='"%Y-%m-%d %H:%M:%S"') + \
                        timedelta(hours=sensor_info['utc_offset'])
        else:
            sample_dt = scanf_datetime(sw[0], fmt='"%Y-%m-%d %H:%M:%S"')

        data['dt'][i] = sample_dt # sample datetime
        data['time'][i] = dt2es(sample_dt) # sample time in epoch seconds

        
        if len(sw)==14:
            # remove all the double quotes (")
            for index, str in enumerate(sw):
                sw[index] = re.sub('\"', '', str)
                
            # >>> sw
            # ['2014-02-01 00:52:01', '77', '$GPRMC', '005155', 'A',
            #        '3443.3939', 'N', '07645.1690', 'W', '000.0', '000.0', '010214', '010.0', 'W']
            # quality of fix

            if sw[4] != 'A':
                data['gps_active'][i] = 0
                print '... Invalid GPS Fix -- skipping line %d' % (i,) 
                continue

            gps_dt_str = sw[11] + ' ' + sw[3] # ddmmyy HHMMSS or ddmmyy HHMMSS.f
            gps_dt = scanf_datetime(gps_dt_str, fmt='%d%m%y %H%M%S')
            if gps_dt == None:
                gps_dt = scanf_datetime(gps_dt_str, fmt='%d%m%y %H%M%S.%f')
                           
            gps_dt.replace(microsecond=0)
            data['gps_dt'][i] = gps_dt # gps fix datetime object    
            data['gps_time'][i] = dt2es(gps_dt) # gps fix time (epoch secs)

            # lat of fix                 
            m = re.search('^(\d{2})(\d+\.\d+)', sw[5])
            if m:
                latdeg = float(m.groups()[0])
                latmin = float(m.groups()[1])
                if sw[6]=='N':
                    data['gps_lat'][i]=latdeg + latmin/60
                else:
                    data['gps_lat'][i]=-1*(latdeg + latmin/60)
            # lon of fix                 
            m = re.search('^(\d{3})(\d+\.\d+)', sw[7])
            if m:
                londeg = float(m.groups()[0])
                lonmin = float(m.groups()[1])
                if sw[8]=='E':
                    data['gps_lon'][i]=londeg + lonmin/60
                else:
                    data['gps_lon'][i]=-1*(londeg + lonmin/60)
            # magnetic variation at fix
            if sw[13]=='E':
                data['gps_mvar'][i] = float(sw[12])
            else:
                data['gps_mvar'][i] = -1*float(sw[12])
            # speed over ground (kts)
            data['gps_sog'][i] = float(sw[9])
            # course over ground or track (deg True N)
            data['gps_cog'][i] = float(sw[10])
            i=i+1
            
        else:
            print ' ... skipping line %d -- %s ' % (i,line)
            continue

        # if re.search
    # for line

    # return the -99999 back into Nan's
    # for vn in ['gps_lat', 'gps_lon', 'gps_mvar', 'gps_cog', 'gps_sog']:
    #     bad = data[vn]==-99999
    #     data[vn][bad] = numpy.nan 

    # or if GPS has no fix and resets to (0,0) coordinates
    for vn in ['gps_lat', 'gps_lon']:
        bad = data[vn]==0
        data[vn][bad] = numpy.nan 

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
        'gps_time' : {'short_name': 'gps_time',
                  'long_name': 'GPS Time',
                  'standard_name': 'time',
                  'units': 'seconds since 1970-1-1 00:00:00 -0', # UTC
                  },
        'gps_lat' : {'short_name': 'gps_lat',
                 'long_name': 'GPS Latitude',
                 'standard_name': 'latitude',
                 'reference':'geographic coordinates',
                 'units': 'degrees_north',
                 'valid_range':(-90.,90.),
                 },
        'gps_lon' : {'short_name': 'gps_lon',
                 'long_name': 'GPS Longitude',
                 'standard_name': 'longitude',
                 'reference':'geographic coordinates',
                 'units': 'degrees_east',
                 'valid_range':(-180.,180.),
                 },
        'gps_mvar' : {'short_name': 'gps_mvar',
                 'long_name': 'GPS Magnetic Variation',
                 'standard_name': 'magnetic_variation',
                 'units': 'degrees',
                 },
        'gps_active' : {'short_name': 'gps_active',
                 'long_name': 'GPS Quality of Fix (active=1 or void=0)',
                 'standard_name': '',
                 'units': '',
                 },
        'gps_sog' : {'short_name': 'gps_sog',
                 'long_name': 'GPS Speed Over Ground',
                 'standard_name': 'speed',
                 'units': 'knots',
                 },
        'gps_cog' : {'short_name': 'gps_cog',
                 'long_name': 'GPS course Over Ground',
                 'reference' : 'clockwise from True North', 
                 'standard_name': 'direction',
                 'units': 'degrees',
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
        ('gps_time', NC.INT, ('ntime',)),
        ('gps_lat', NC.FLOAT, ('ntime',)),
        ('gps_lon', NC.FLOAT, ('ntime',)),
        ('gps_mvar', NC.FLOAT, ('ntime',)),
        ('gps_active', NC.FLOAT, ('ntime',)),
        ('gps_sog', NC.FLOAT, ('ntime',)),
        ('gps_cog', NC.FLOAT, ('ntime',)),
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
        ('gps_time', data['gps_time'][i]),
        ('gps_lat', data['gps_lat'][i]),
        ('gps_lon', data['gps_lon'][i]),
        ('gps_active', data['gps_active'][i]),
        ('gps_sog', data['gps_sog'][i]),
        ('gps_cog', data['gps_cog'][i]),
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
        ('gps_time', data['gps_time'][i]),
        ('gps_lat', data['gps_lat'][i]),
        ('gps_lon', data['gps_lon'][i]),
        ('gps_active', data['gps_active'][i]),
        ('gps_sog', data['gps_sog'][i]),
        ('gps_cog', data['gps_cog'][i]),
        )

    return (global_atts, var_atts, var_data)
#
