#!/usr/bin/env python
# Last modified:  Time-stamp: <2008-10-16 14:06:06 haines>
"""
how to parse data, and assert what data and info goes into
creating and updating monthly netcdf files

RDI/Wavesmon processed adcp current profile data

parser : sample date and time, ensemble number, currents
         and wave summary output from WavesMon software
creator : lat, lon, z, time, ens, u, v
updator : time, ens, u, v


Examples
--------

>> (parse, create, update) = load_processors('proc_rdi_logdata_adcp')
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
    parse and assign currents data from RDI ADCP Log Data

    """
 
    i = 0
   
    for line in lines:
        # split line and parse float and integers
        rdi = []
        sw = re.split(',', line)
        for s in sw:
            m = re.search(REAL_RE_STR, s)
            if m:
                rdi.append(float(m.groups()[0]))

        # assign specific fields
        n = len(rdi)
        burst_num = int(rdi[0]) # Ensemble Number

        # get sample datetime from data
        sample_str = '%02d-%02d-%02d %02d:%02d:%02d' % tuple(rdi[1:7])
        if  sensor_info['utc_offset']:
            sample_dt = scanf_datetime(sample_str, fmt='%y-%m-%d %H:%M:%S') + \
                        timedelta(hours=sensor_info['utc_offset'])
        else:
            sample_dt = scanf_datetime(sample_str, fmt='%y-%m-%d %H:%M:%S')
        #   datetime(*strptime(sample_str, "%y-%m-%d %H:%M:%S")[0:6])

        # get sample datetime from filename
        # compare with datetime from filename 

        sig_wave_ht = rdi[8]         # Significant Wave Height (Hs, meters)
        peak_wave_period = rdi[9]    # Peak Wave Period (Tp, sec)
        peak_wave_dir = rdi[10]      # Peak Wave Direction (deg N)
        max_wave_ht = rdi[12]        # Maximum Wave Height (Hmax, meters)
        max_wave_period = rdi[13]    # Maximum Wave Period (Tmax, sec)

        wd = rdi[11]/1000   # Water Depth (meters) (based on ADCP backscatter or input config??)
                            # This includes height of transducer
        nbins = int(rdi[14])         # Number of bins

        current_spd = numpy.array(rdi[15::2]) # starting at idx=15 skip=2 to end
        current_dir = numpy.array(rdi[16::2]) # starting at idx=16 skip=2 to end

        if nbins!=sensor_info['nbins']:
            print 'Number of bins reported in data ('+ \
                  str(nbins)+') does not match config number ('+ \
                  str(sensor_info['nbins'])+')'

        if len(current_spd)!=nbins or len(current_dir)!=nbins:
            print 'Data length does not match number of bins in data'

        ibad = (current_spd==-32768) | (current_dir==-32768)
        current_spd[ibad] = numpy.nan
        current_dir[ibad] = numpy.nan

        # these items can also be teased out of raw adcp but for now get from config file
        th = sensor_info['transducer_ht']  # Transducer height above bottom (meters)
        bh = sensor_info['blanking_ht']    # Blanking height above Transducer (meters)
        bin_size = sensor_info['bin_size'] # Bin Size (meters)

        # compute height for each bin above the bottom
        bins = numpy.arange(1,nbins+1)
        bin_habs = (bins*bin_size+bin_size/2)+th+bh

        # compute water mask 
        # Using George Voulgaris' method based on water depth
        # minus half of the significant wave height (Hs)
        # and computed habs
        # if positive is up, what's less than zero depth?

        # added by SH -- 15 Oct 2008
        # raw2proc:ticket:27 adjust bin_habs along beam to nadir
        # adjustment is cos(20 deg) (which is  approx .95*height) assuming fixed 20 deg
        bin_habs =  bin_habs*numpy.cos(20.*numpy.pi/180)
        bin_depths =  bin_habs-(wd)
        iwater = bin_depths+bin_size/2 < 0

        # use nominal water depth (MSL) averaged from full pressure record
        #  this should be checked/recalulated every so often
        z = bin_habs + platform_info['mean_water_depth']  # meters, (+) up, (-) down

        # check that length of bin_depths is equal to nbins
        u = numpy.ones(nbins)*numpy.nan
        v = numpy.ones(nbins)*numpy.nan

        u[iwater] = current_spd[iwater]*numpy.sin(current_dir[iwater]*numpy.pi/180)
        v[iwater] = current_spd[iwater]*numpy.cos(current_dir[iwater]*numpy.pi/180)

        # set up dict of data if first line
        if i==0:
            data = {
                'en' : numpy.array(numpy.ones((len(lines),), dtype=int)*numpy.nan),
                'dt' : numpy.array(numpy.ones((len(lines),), dtype=object)*numpy.nan),
                'time' : numpy.array(numpy.ones((len(lines),), dtype=long)*numpy.nan),
                'z' : numpy.array(numpy.ones((nbins,), dtype=float)*numpy.nan),
                'u' : numpy.array(numpy.ones((len(lines),nbins), dtype=float)*numpy.nan),
                'v' : numpy.array(numpy.ones((len(lines),nbins), dtype=float)*numpy.nan),
                'wd' : numpy.array(numpy.ones((len(lines)), dtype=float)*numpy.nan),
                'wl' : numpy.array(numpy.ones((len(lines)), dtype=float)*numpy.nan),
                }
        
        data['en'][i] = burst_num
        data['dt'][i] = sample_dt # sample datetime
        data['time'][i] = dt2es(sample_dt) # sample time in epoch seconds
        data['z'] =  z
        data['u'][i] =  u
        data['v'][i] =  v
        data['wd'][i] = -1*wd
        data['wl'][i] = platform_info['mean_water_depth'] - (-1*wd)  
        i = i+1

    return data

def creator(platform_info, sensor_info, data):
    #
    # 
    title_str = sensor_info['description']+' at '+ platform_info['location']

    if 'mean_water_depth' in platform_info.keys():
        msl_str = platform_info['mean_water_depth']
    else:
        msl_str = 'None'
    if 'mean_water_depth_time_period' in platform_info.keys():
        msl_tp_str = platform_info['mean_water_depth_time_period']
    else:
        msl_tp_str = 'None'
        
    global_atts = { 
        'title' : title_str,
        'institution' : 'University of North Carolina at Chapel Hill (UNC-CH)',
        'institution_url' : 'http://nccoos.unc.edu',
        'institution_dods_url' : 'http://nccoos.unc.edu',
        'metadata_url' : 'http://nccoos.unc.edu',
        'references' : 'http://nccoos.unc.edu',
        'contact' : 'Sara Haines (haines@email.unc.edu)',
        # 
        'source' : 'fixed-profiler (acoustic doppler) observation',
        'history' : 'raw2proc using ' + sensor_info['process_module'],
        'comment' : 'File created using pycdf'+pycdfVersion()+' and numpy '+pycdfArrayPkg(),
        # conventions
        'Conventions' : 'CF-1.0; SEACOOS-CDL-v2.0',
        # SEACOOS CDL codes
        'format_category_code' : 'fixed-profiler',
        'institution_code' : platform_info['institution'],
        'platform_code' : platform_info['id'],
        'package_code' : sensor_info['id'],
        # institution specific
        'project' : 'North Carolina Coastal Ocean Observing System (NCCOOS)',
        'project_url' : 'http://nccoos.unc.edu',
        # timeframe of data contained in file yyyy-mm-dd HH:MM:SS
        # first date in monthly file
        'start_date' : data['dt'][0].strftime("%Y-%m-%d %H:%M:%S"),
        # last date in monthly file
        'end_date' : data['dt'][-1].strftime("%Y-%m-%d %H:%M:%S"), 
        'release_date' : now_dt.strftime("%Y-%m-%d %H:%M:%S"),
        # 
        'mean_water_depth' : msl_str,
        'mean_water_depth_time_period' : msl_tp_str,
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
               'long_name': 'Height',
               'standard_name': 'height',
               'reference':'zero at sea-surface',
               'units': 'm',
               'axis': 'Z',
               },
        # data variables
        'en' : {'short_name' : 'en',
                'long_name': 'Ensemble Number',
                 'standard_name': 'ensemble_number',                          
                 'units': 'None',
                 },
        'u': {'short_name' : 'u',
              'long_name': 'East/West Component of Current',
              'standard_name': 'eastward_current',
              'units': 'm s-1',
              'reference': 'clockwise from True East',
              },
        'v': {'short_name' : 'v',
              'long_name': 'North/South Component of Current',
              'standard_name': 'northward_current',                          
              'units': 'm s-1',
              'reference': 'clockwise from True North',
              },
        'wd': {'short_name': 'wd',
               'long_name': 'Water Depth',
               'standard_name': 'water_depth',                          
               'reference':'zero at surface',
               'positive' : 'up',
               'units': 'm',
               },
        'wl': {'short_name': 'wl',
               'long_name': 'Water Level',
               'standard_name': 'water_level',                          
               'reference':'MSL',
               'reference_to_MSL' : 0.,
               'reference_MSL_datum' : platform_info['mean_water_depth'],
               'reference_MSL_datum_time_period' : platform_info['mean_water_depth_time_period'],
               'positive' : 'up',
               'z' : 0., 
               'units': 'm',
               },
        }


    # dimension names use tuple so order of initialization is maintained
    dim_inits = (
        ('ntime', NC.UNLIMITED),
        ('nlat', 1),
        ('nlon', 1),
        ('nz', sensor_info['nbins'])
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
        ('en', NC.INT, ('ntime', )),
        ('u', NC.FLOAT, ('ntime', 'nz')),
        ('v', NC.FLOAT, ('ntime', 'nz')),
        ('wd', NC.FLOAT, ('ntime',)),
        ('wl', NC.FLOAT, ('ntime',)),
        )

    # subset data only to month being processed (see raw2proc.process())
    i = data['in']
    
    # var data 
    var_data = (
        ('lat',  platform_info['lat']),
        ('lon', platform_info['lon']),
        ('z', data['z']),
        #
        ('time', data['time'][i]),
        ('en', data['en'][i]),
        ('u', data['u'][i]),
        ('v', data['v'][i]),
        ('wd', data['wd'][i]),
        ('wl', data['wl'][i]),
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
        ('en', data['en'][i]),
        ('u', data['u'][i]),
        ('v', data['v'][i]),
        ('wd', data['wd'][i]),
        ('wl', data['wl'][i]),
        )

    return (global_atts, var_atts, var_data)
#
