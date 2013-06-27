#!/usr/bin/env python
# Last modified:  Time-stamp: <2012-06-28 14:47:42 haines>
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
    "TOA5","CR1000_B1","CR1000","37541","CR1000.Std.21","CPU:NCWIND_12_Buoy_All.CR1","58723","CTD1_6Min"
    "TIMESTAMP","RECORD","ID","Temp","Cond","Depth","SampleDate","SampleTime","SampleNum"
    "TS","RN","","","","","","",""
    "","","Smp","Smp","Smp","Smp","Smp","Smp","Smp"
    "2011-10-05 21:08:06",43,4085,24.5027,5.18209,3.347
    "2011-10-05 21:14:06",44,4085,24.5078,5.18305,3.454
    "2011-10-05 21:56:07",45,4085,24.5247,5.19257,3.423
    "2011-10-05 22:02:06",46,4085,24.5105,5.18714,3.526
    "2011-10-05 22:08:07",47,4085,24.519,5.19096,3.547
    "2011-10-05 22:14:06",48,4085,24.5207,5.19172,3.508

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
        'wtemp' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'cond' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'press' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'salin' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'density' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'depth' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        }

    # sample count
    i = 0

    for line in lines[4:]:
        csi = []
        # split line
        sw = re.split(',', line)
        if len(sw)<=0:
            print ' ... skipping line %d -- %s' % (i,line)
            continue

        # replace "NAN"
        for index, s in enumerate(sw):
            m = re.search(NAN_RE_STR, s)
            if m:
                sw[index] = '-99999'

        # parse date-time, and all other float and integers
        for s in sw[1:6]:
            m = re.search(REAL_RE_STR, s)
            if m:
                csi.append(float(m.groups()[0]))

        if len(sw)>=6:
            dstr = re.sub('"', '', sw[0])
            # print dstr
        else:
            print ' ... skipping line %d -- %s ' % (i,line)
            continue            

        if  sensor_info['utc_offset']:
            sample_dt = scanf_datetime(dstr, fmt='%Y-%m-%d %H:%M:%S') + \
                        timedelta(hours=sensor_info['utc_offset'])
        else:
            sample_dt = scanf_datetime(dstr, fmt='%Y-%m-%d %H:%M:%S')

        # ***** TO DO: need to adjust any drift of offset in CTD sample time to CR1000 clock
        data['dt'][i] = sample_dt # sample datetime
        data['time'][i] = dt2es(sample_dt) # sample time in epoch seconds

        if len(csi)==5:
            #
            # (pg 31 SBE IMP Microcat User Manual)
            # "#iiFORMAT=1 (default) Output converted to data
            # date format dd mmm yyyy,
            # conductivity = S/m,
            # temperature precedes conductivity"
            sn = csi[1] # ctd serial number == check against platform configuration
            data['wtemp'][i] =  csi[2] # water temperature (C)
            data['cond'][i] = csi[3] # specific conductivity (S/m)
            data['press'][i] = csi[4]   # pressure decibars 
            i=i+1
        else:
            print ' ... skipping line %d -- %s ' % (i,line)
            continue            
            
        # if re.search
    # for line

    # check that no data[dt] is set to Nan or anything but datetime
    # keep only data that has a resolved datetime
    keep = numpy.array([type(datetime(1970,1,1)) == type(dt) for dt in data['dt'][:]])
    if keep.any():
        for param in data.keys():
            data[param] = data[param][keep]

    # Quality Control steps for temp, depth, and cond 
    # (1) within range
    # (2) if not pumped 
    good = (5<data['wtemp']) & (data['wtemp']<30)
    bad = ~good
    data['wtemp'][bad] = numpy.nan
    
    good = (2<data['cond']) & (data['cond']<7)
    bad = ~good
    data['cond'][bad] = numpy.nan
    
    # calculate depth, salinity and density    
    import seawater.csiro
    import seawater.constants

    # seawater.constants.C3515 is units of mS/cm
    # data['cond'] is units of S/m
    # You have: mS cm-1
    # You want: S m-1
    #     <S m-1> = <mS cm-1>*0.1
    #     <S m-1> = <mS cm-1>/10

    data['depth'] = -1*seawater.csiro.depth(data['press'], platform_info['lat']) # meters
    data['salin'] = seawater.csiro.salt(10*data['cond']/seawater.constants.C3515, data['wtemp'], data['press']) # psu
    data['density'] = seawater.csiro.dens(data['salin'], data['wtemp'], data['press']) # kg/m^3

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
               'long_name': 'Depth',
               'standard_name': 'depth',
               'reference':'zero at sea-surface',
               'positive' : 'up',
               'units': 'm',
               'axis': 'Z',
               },
        # data variables
        'wtemp': {'short_name': 'wtemp',
                  'long_name': 'Water Temperature',
                  'standard_name': 'water_temperature',                          
                  'units': 'degrees_Celsius',
                  },
        'cond': {'short_name': 'cond',
                 'long_name': 'Conductivity',
                 'standard_name': 'conductivity',                          
                 'units': 'S m-1',
                 },
        'press': {'short_name': 'press',
                 'long_name': 'Pressure',
                 'standard_name': 'water_pressure',                          
                 'units': 'decibar',
                 },
        'depth': {'short_name': 'depth',
                  'long_name': 'Depth',
                  'standard_name': 'depth',                          
                  'reference':'zero at sea-surface',
                  'positive' : 'up',
                  'units': 'm',
                  'comment': 'Derived using seawater.csiro.depth(press,lat)',
                 },
        'salin': {'short_name': 'salin',
                  'long_name': 'Salinity',
                  'standard_name': 'salinity',
                  'units': 'psu',
                  'comment': 'Derived using seawater.csiro.salt(cond/C3515,wtemp,press)',
                 },
        'density': {'short_name': 'density',
                    'long_name': 'Density',
                    'standard_name': 'density',
                    'units': 'kg m-3',
                    'comment': 'Derived using seawater.csiro.dens0(salin,wtemp,press)',
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
        ('wtemp', NC.FLOAT, ('ntime',)),
        ('cond', NC.FLOAT, ('ntime',)),
        ('press', NC.FLOAT, ('ntime',)),
        # derived variables
        ('depth', NC.FLOAT, ('ntime',)),
        ('salin', NC.FLOAT, ('ntime',)),
        ('density', NC.FLOAT, ('ntime',)),
        )

    # var data 
    var_data = (
        ('lat',  platform_info['lat']),
        ('lon', platform_info['lon']),
        ('z', sensor_info['nominal_depth']),
        #
        ('time', data['time'][i]),
        #
        ('wtemp', data['wtemp'][i]),
        ('cond', data['cond'][i]),
        ('press', data['press'][i]),
        # derived variables
        ('depth', data['depth'][i]),
        ('salin',  data['salin'][i]),
        ('density', data['density'][i]),
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
        ('wtemp', data['wtemp'][i]),
        ('cond', data['cond'][i]),
        ('press', data['press'][i]),
        # derived variables
        ('depth', data['depth'][i]),
        ('salin',  data['salin'][i]),
        ('density', data['density'][i]),
        )

    return (global_atts, var_atts, var_data)
#
