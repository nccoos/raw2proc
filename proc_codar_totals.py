#!/usr/bin/env python
# Last modified:  Time-stamp: <2013-04-30 16:27:48 haines>
"""
how to parse data, and assert what data and info goes into
creating and updating monthly netcdf files

CODAR SeaSonde Total Sea Surface Currents (LLUV TOT4) 

parser : sample date and time from header (%TimeStamp:)
         table time version (%TableType:)
creator : lat, lon, z, time, u(time, lat, lon), v(time, lat, lon),
updater : time, u(time, lat, lon), v(time, lat, lon),

Check that grid that totals are calculated over has not changed.
(%Origin, %GridAxis, %GridAxisType, %GridSpacing all the same)

Examples
--------

>> (parse, create, update) = load_processors(module_name_without_dot_py)
For example, 
>> (parse, create, update) = load_processors('proc_rdi_logdata_adcp')
or
>> si = get_config(cn+'.sensor_info')
>> (parse, create, update) = load_processors(si['adcp']['proc_module'])

Then use the generic name of processor to parse data, create or update
monthly output file

>> lines = load_data(filename)
>> data = parse(platform_info, sensor_info, lines)
>> create(platform_info, sensor_info, data)
or
>> update(platform_info, sensor_info, data)

"""

from raw2proc import *
from procutil import *
from ncutil import *

now_dt = datetime.utcnow()
now_dt.replace(microsecond=0)

def parser(platform_info, sensor_info, lines):
    """
    parse and assign data to variables from CODAR Totals LLUV format

    Notes
    -----
    1. Requires grid definition obtained from sensor_info
    For best coverage of totals, this includes overlapping foot print of HATY, DUCK, LISL and CEDR
    
    """

    import numpy
    from datetime import datetime
    from time import strptime
    from StringIO import StringIO
    from matplotlib.mlab import griddata

    # define the lat/lon grid based on 6km resolution
    minlat, maxlat = platform_info['lat'] # (34.5, 38)
    minlon, maxlon = platform_info['lon'] # (-76, -73.)
    nlat = platform_info['nlat']
    nlon = platform_info['nlon']
    yi = numpy.linspace(minlat, maxlat, nlat)
    xi = numpy.linspace(minlon, maxlon, nlon)
    xmesh, ymesh = numpy.meshgrid(xi, yi)

    data = {
        'dt' : numpy.array(numpy.ones((1,), dtype=object)*numpy.nan),
        'time' : numpy.array(numpy.ones((1,), dtype=long)*numpy.nan),
        'lon' : numpy.array(numpy.ones((nlon,), dtype=float)*numpy.nan),
        'lat' : numpy.array(numpy.ones((nlat,), dtype=float)*numpy.nan),
        'u' : numpy.array(numpy.ones((1,nlon,nlat), dtype=float)*numpy.nan),
        'v' : numpy.array(numpy.ones((1,nlon,nlat), dtype=float)*numpy.nan),
        }

    sample_dt, ftype, lluvspec, ncol, nrow = (None, None, None, None, None)
    # read header that match '%(k): (v)\n' pairs on each line
    m = re.findall(r'^(%.*):\s*(.*)$', ''.join(lines), re.MULTILINE)
    for k,v in m:
        if k == '%TimeStamp':
            sample_dt = scanf_datetime(v, fmt='%Y %m %d %H %M %S')            
        elif k == '%TableType':
            ftype = v
        elif k == '%LLUVSpec':
            lluvspec = float(re.split('\s+', v)[0])
        elif k == '%TableColumns':
            ncol = int(v)
        elif k == '%TableRows':
            nrow = int(v)
        elif k == '%TableEnd':
            break
            # LLUVSpec 1.17 and greater has two tables bracketed by TableStart and TableEnd
            # get out of this search loop after the first table 

    if nrow>2:
        # read data from string of lines but make it behave like a file object with StringIO
        s = StringIO(''.join(lines))
        s.seek(0) # ensures start posn of file
        d = numpy.loadtxt(s, comments='%')
        # lat, lon, u, v = numpy.loadtxt(s, usecols=(0,1,2,3), comments='%', unpack=True)
        
        if 'TOT4' in ftype:
            lon = d[:,0]
            lat = d[:,1]
            wu = d[:,2]
            wv = d[:,3]
            gridflag = d[:,4]
            wu_std_qual = d[:,5]
            wv_std_qual = d[:,6]
            cov_qual = d[:,7]
            x_dist = d[:,8]
            y_dist = d[:,9]
            rang = d[:,10]
            bearing = d[:,11]
            vel_mag = d[:,12]
            vel_dir = d[:,13]

        # ibad = (wu_std_qual==999.) | (wv_std_qual==999.) | (cov_qual==999.) 
        # wu[ibad] = numpy.nan
        # wv[ibad] = numpy.nan

        # SMH -- April 26, 2013 -- commenting out these columns for now until figure out how to handle
        # new dynamic form of LLUVSpec 1.17 in TOT4 format, prior versions were static with 6 fields
        # will have to use %LLUVSpec header info and second table at bottom of file to get dynamic ncols 
            # s1 = d[:,14]
            # s2 = d[:,15]
            # s3 = d[:,16]
            # s4 = d[:,17]
            # s5 = d[:,18]
            # s6 = d[:,19]

            try: 
                uim = griddata(lon, lat, wu, xmesh, ymesh)
                vim = griddata(lon, lat, wv, xmesh, ymesh)
                # returned masked array as an ndarray with masked values filled with fill_value
                ui = uim.filled(fill_value=numpy.nan)
                vi = vim.filled(fill_value=numpy.nan)
                # print ui.shape
            except IndexError:
                print "raw2proc:  IndexError in griddata() -- skipping data"

    # ---------------------------------------------------------------
    i = 0
    data['dt'][i] =  sample_dt # 
    data['time'][i] =  dt2es(sample_dt) # 
    data['lon'] = xi # new longitude grid
    data['lat'] = yi # new latitude grid

    if nrow and nrow>2:
        # use transpose so order is (time, x, y) for netcdf convention
        data['u'][i] = ui.T # u-component of water velocity (cm/s)
        data['v'][i] = vi.T # v-component of water velocity 

    return data

def creator(platform_info, sensor_info, data):
    #
    # 
    title_str = sensor_info['description']+' at '+ platform_info['location']
    global_atts = { 
        'title' : title_str,
        'institution' : 'University of North Carolina at Chapel Hill (UNC-CH)',
        'institution_url' : 'http://nccoos.unc.edu',
        'institution_dods_url' : 'http://nccoos.unc.edu',
        'metadata_url' : 'http://nccoos.unc.edu',
        'references' : 'http://nccoos.unc.edu',
        'contact' : 'Sara Haines (haines@email.unc.edu)',
        # 
        'source' : 'surface current observation',
        'history' : 'raw2proc using ' + sensor_info['process_module'],
        'comment' : 'File created using pycdf'+pycdfVersion()+' and numpy '+pycdfArrayPkg(),
        # conventions
        'Conventions' : 'CF-1.0; SEACOOS-CDL-v2.0',
        # SEACOOS CDL codes
        'format_category_code' : 'fixed-map',
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
        '_FillValue' : numpy.nan,
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
               'long_name': 'Height',
               'standard_name': 'height',
               'reference':'zero at sea-surface',
               'units': 'm',
               'axis': 'Z',
               },
        # data variables
        'u' : {'short_name': 'u',
               'long_name': 'E/W component of current',
               'standard_name': 'eastward_current',
               'units': 'cm sec-1',
               'reference' : 'clockwise from True East',
                },
        'v' : {'short_name': 'v',
               'long_name': 'N/S component of current',
               'standard_name': 'northward_current',
               'units': 'cm sec-1',
               'reference' : 'clockwise from True North',
                },
        }

    
    # dimension names use tuple so order of initialization is maintained
    dim_inits = (
        ('ntime', NC.UNLIMITED),
        ('nlat', platform_info['nlat']),
        ('nlon', platform_info['nlon']),
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
        ('u', NC.FLOAT, ('ntime','nlon','nlat')),
        ('v', NC.FLOAT, ('ntime','nlon','nlat')),
        )
    
    # subset data only to month being processed (see raw2proc.process())
    i = data['in']

    # var data 
    var_data = (
        ('lat', data['lat']),
        ('lon', data['lon']),
        ('z', 0.),
        #
        ('time', data['time'][i]),
        ('u', data['u'][i]),
        ('v', data['v'][i]),
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
    #    'u': {'max': max(data.u),
    #          'min': min(data.v),
    #          },
    #    'v': {'max': max(data.u),
    #          'min': min(data.v),
    #          },
    #    }
    
    # subset data only to month being processed (see raw2proc.process())
    i = data['in']

    # data 
    var_data = (
        ('time', data['time'][i]),
        ('u', data['u'][i]),
        ('v', data['v'][i]),
       )

    return (global_atts, var_atts, var_data)

#
