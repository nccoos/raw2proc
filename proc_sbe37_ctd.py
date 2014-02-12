#!/usr/bin/env python
# Last modified:  Time-stamp: <2014-01-09 15:05:20 haines>
"""
how to parse data, and assert what data and info goes into
creating and updating monthly netcdf files

parse data ctd data collected on Seabird CTD -- SBE37
derive salinity, depth, and density using seawater.csiro toolbox

parser : sample date and time, wtemp, cond, press, (derive) depth, salin, dens

creator : lat, lon, z, time, wtemp, cond, press, depth, salin, dens
updator : time, wtemp, cond, press, depth, salin, dens

Examples
--------
>>> sensor_info = sensor_info['ctd1']
>>> (parse, create, update) = import_processors(sensor_info['process_module'])

>>> data = parse(platform_info, sensor_info, lines)
>>> create(platform_info, sensor_info, data) or
>>> update(platform_info, sensor_info, data)

Testing
-------
from raw2proc import *
cn = 'b1_config_20111112'
sensor_info = get_config(cn+'.sensor_info')
sensor_info = sensor_info['ctd1']
platform_info = get_config(cn+'.platform_info')
(parse, create, update) = import_processors(sensor_info['process_module'])

filename = '/seacoos/data/nccoos/level0/b1/ctd1/store/B1_CTD1_2011_11_12.asc'
lines = load_data(filename)
sensor_info['fn'] = filename
data = parse(platform_info, sensor_info, lines)

create(platform_info, sensor_info, data)
update(platform_info, sensor_info, data)

"""
from raw2proc import *
from procutil import *
from ncutil import *

now_dt = datetime.utcnow()
now_dt.replace(microsecond=0)

def parser(platform_info, sensor_info, lines):
    """
    Header comments start with '*'
    Last line of comments *END*
    
    * Sea-Bird SBE37 Data File:
    * FileName = C:\Documents and Settings\haines\Desktop\nc-wind 2012 CTD Recovery\B1_CTD1_3085_2012-04-07.asc
    ...
    * S>
    *END*
    start time =  12 Nov 2011  15:28:43
    sample interval = 360 seconds
    start sample number = 1
    17.4036,  4.35264,    3.521, 12 Nov 2011, 15:28:43
    17.4289,  4.35624,    3.593, 12 Nov 2011, 15:34:44
    17.4110,  4.35376,    3.600, 12 Nov 2011, 15:40:44
    17.4106,  4.35395,    3.618, 12 Nov 2011, 15:46:44
    17.3798,  4.34961,    3.515, 12 Nov 2011, 15:52:44
    17.3861,  4.35033,    3.708, 12 Nov 2011, 15:58:44
    17.4136,  4.35348,    3.488, 12 Nov 2011, 16:04:44
    17.4269,  4.35530,    3.616, 12 Nov 2011, 16:10:44
    17.4421,  4.35679,    3.612, 12 Nov 2011, 16:16:44
    17.4417,  4.35679,    3.537, 12 Nov 2011, 16:22:44
    ... EOF                    

    """

    import numpy
    from datetime import datetime
    from time import strptime

    # get sample datetime from filename
    fn = sensor_info['fn']
    sample_dt_start = filt_datetime(fn)

    # tease out the header info and where it ends
    # **** may want more info extracted later for data attributes (e.g. sensor coeff)
    serial_number, end_idx, sample_interval_str = (None, None, None)
    for idx, k in enumerate(lines[0:100]):
        # serial number
        m = re.search(r'^\*.*(SERIAL NO\.)\s+(\d*)', k)
        if m: serial_number = m.group(2)
        m = re.search(r'^\*\w+(sample interval)\s*=\s*(.*)', k)
        if m: sample_interval_str = m.group(2)
        m = re.search(r'^(\*END\*).*', k)
        if m: end_idx = idx
    # check that serial_info serial_number, sample_interval matches 

    # split data from header info and get how many samples (start count 3 lines past *END*)
    if end_idx: lines = lines[end_idx+3:]
    nsamp = len(lines)

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

    for line in lines:
        # if line has weird ascii chars -- skip it and iterate to next line
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
        for s in sw[0:3]:
            m = re.search(REAL_RE_STR, s)
            if m:
                csi.append(float(m.groups()[0]))

        if len(sw)>=5:
            dstr = sw[3]+' '+sw[4]
            # print dstr
            m = re.search('\s*(\d{2})\s*(\w{2,3})\s*(\d{4})\s*(\d{2}):(\d{2}):(\d{2}).*', dstr)
        else:
            print ' ... skipping line %d -- %s ' % (i,line)
            continue            

        if m:
            dstr = '%s %s %s %s:%s:%s' % m.groups()
        else:
            print ' ... skipping line %d -- %s ' % (i,line)
            continue            

        if  sensor_info['utc_offset']:
            sample_dt = scanf_datetime(dstr, fmt='%d %b %Y %H:%M:%S') + \
                        timedelta(hours=sensor_info['utc_offset'])
        else:
            sample_dt = scanf_datetime(dstr, fmt='%d %b %Y %H:%M:%S')

        # ***** TO DO: may need to adjust any offset in CTD sample time to UTC clock
        # This requires knowing what UTC time is at a CTD sample 
        data['dt'][i] = sample_dt # sample datetime
        data['time'][i] = dt2es(sample_dt) # sample time in epoch seconds

        if len(csi)==3:
            #
            # (pg 31 SBE IMP Microcat User Manual)
            # "#iiFORMAT=1 (default) Output converted to data
            # date format dd mmm yyyy,
            # conductivity = S/m,
            # temperature precedes conductivity"
            data['wtemp'][i] =  csi[0] # water temperature (C)
            data['cond'][i] = csi[1] # specific conductivity (S/m)
            data['press'][i] = csi[2]   # pressure decibars 
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
    good = (-5<data['wtemp']) & (data['wtemp']<30)
    bad = ~good
    data['wtemp'][bad] = numpy.nan 
    
    good = (0<data['cond']) & (data['cond']<7)
    bad = ~good
    data['cond'][bad] = numpy.nan

    # press range depends on deployment depth and instrument transducer rating
    
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
