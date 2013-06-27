#!/usr/bin/env python
# Last modified:  Time-stamp: <2008-10-01 12:47:50 haines>
"""
how to parse data, and assert what data and info goes into
creating and updating monthly netcdf files

RDI/Wavesmon processed adcp current profile data

parser : sample date and time, ensemble number, wave summary output from WavesMon software
creator : lat, lon, z, time, sig_wave_ht, peak_wave_period, peak_wave_dir,
          max_wave_ht, max_wave_period, water_depth
updater : time, sig_wave_ht, peak_wave_period, peak_wave_dir,
          max_wave_ht, max_wave_period, water_depth

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
        mean_wave_period = rdi[13]    # Maximum Wave Period (Tmean, sec)

        water_depth = rdi[11]/1000   # Water Depth (meters) (based on ADCP backscatter or input config??)
        nbins = int(rdi[14])         # Number of bins

        # set up dict of data if first line
        if i==0:
            data = {
                'en' : numpy.array(numpy.ones((len(lines),), dtype=int)*numpy.nan),
                'dt' : numpy.array(numpy.ones((len(lines),), dtype=object)*numpy.nan),
                'time' : numpy.array(numpy.ones((len(lines),), dtype=long)*numpy.nan),
                'sig_wave_ht' : numpy.array(numpy.ones((len(lines)), dtype=float)*numpy.nan),
                'peak_wave_period' : numpy.array(numpy.ones((len(lines)), dtype=float)*numpy.nan),
                'peak_wave_dir' : numpy.array(numpy.ones((len(lines)), dtype=float)*numpy.nan),
                'max_wave_ht' : numpy.array(numpy.ones((len(lines)), dtype=float)*numpy.nan),
                'mean_wave_period' : numpy.array(numpy.ones((len(lines)), dtype=float)*numpy.nan),
                'water_depth' : numpy.array(numpy.ones((len(lines)), dtype=float)*numpy.nan),
                }
        
        data['en'][i] = burst_num
        data['dt'][i] = sample_dt # sample datetime
        data['time'][i] = dt2es(sample_dt) # sample time in epoch seconds
        data['sig_wave_ht'][i] = sig_wave_ht
        data['peak_wave_period'][i] = peak_wave_period
        data['peak_wave_dir'][i] = peak_wave_dir
        data['max_wave_ht'][i] =  max_wave_ht
        data['mean_wave_period'][i] =  mean_wave_period
        data['water_depth'][i] = water_depth 
        i = i+1

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
        'source' : 'directional wave (acoustic doppler) observation',
        'history' : 'raw2proc using ' + sensor_info['process_module'],
        'comment' : 'File created using pycdf'+pycdfVersion()+' and numpy '+pycdfArrayPkg(),
        # conventions
        'Conventions' : 'CF-1.0; SEACOOS-CDL-v2.0',
        # SEACOOS CDL codes
        'format_category_code' : 'directional waves',
        'institution_code' : platform_info['institution'],
        'platform_code' : platform_info['id'],
        'package_code' : sensor_info['id'],
        # institution specific
        'project' : 'North Carolina Coastal Ocean Observing System (NCCOOS)',
        'project_url' : 'http://nccoos.unc.edu',
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
        'en' : {'short_name': 'en',
                'long_name': 'Ensemble Number',
                'standard_name': 'ensemble_number',                          
                'units': 'None',
                 },
        'sig_wave_ht' : {'short_name': 'Hs',
                         'long_name': 'Significant Wave Height',
                         'definition': 'Four times the square root of the first moment of the wave spectrum (4*sqrt(m0))',
                         'standard_name': 'significant_wave_height',
                         'units': 'm',
                        },
        'peak_wave_period' : {'short_name': 'Tp',
                             'long_name': 'Peak Wave Period',
                             'definition': 'Period of strongest wave (wave energy maximum)',
                             'standard_name': 'peak_wave_period',                          
                             'units': 'sec',
                             },
        'peak_wave_dir' : {'short_name': 'Dp',
                           'long_name': 'Peak Wave Direction',
                           'definition': 'Direction from which strongest waves (wave energy max) are coming',
                           'standard_name': 'peak_wave_from_direction',                          
                           'units': 'deg from N',
                           'reference': 'clockwise from True North',
                           },
        'max_wave_ht' : {'short_name': 'Hmax',
                         'long_name': 'Maximum Wave Height',
                         'standard_name': 'max_wave_height',                          
                         'units': 'm',
                         },
        'mean_wave_period' : {'short_name': 'Tmean',
                              'long_name': 'Mean Wave Period',
                              'definition': 'Zero-moment of the non-directional spectrum divided by the first-moment (m0/m1)',
                              'standard_name': 'mean_wave_period',                          
                              'units': 'sec',
                              },
        'water_depth': {'short_name': '',
                        'long_name': 'Water Depth',
                        'standard_name': 'water_depth',                          
                        'units': 'm',
                        },

        }


    # integer values 
    ntime=NC.UNLIMITED
    nlat=1
    nlon=1
    nz=1
    
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
        ('en', NC.INT, ('ntime', )),
        ('sig_wave_ht', NC.FLOAT, ('ntime',)),
        ('peak_wave_period', NC.FLOAT, ('ntime',)),
        ('peak_wave_dir', NC.FLOAT, ('ntime',)),
        ('max_wave_ht', NC.FLOAT, ('ntime',)),
        ('mean_wave_period', NC.FLOAT, ('ntime',)),
        ('water_depth', NC.FLOAT, ('ntime',)),
        )
    
    # subset data only to month being processed (see raw2proc.process())
    i = data['in']

    # var data 
    var_data = (
        ('lat',  platform_info['lat']),
        ('lon', platform_info['lon']),
        ('z', 0),
        #
        ('time', data['time'][i]),
        ('en', data['en'][i]),
        ('sig_wave_ht', data['sig_wave_ht'][i]),
        ('peak_wave_period', data['peak_wave_period'][i]),
        ('peak_wave_dir', data['peak_wave_dir'][i]),
        ('max_wave_ht', data['max_wave_ht'][i]),
        ('mean_wave_period', data['mean_wave_period'][i]),
        ('water_depth', data['water_depth'][i]),
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
        ('sig_wave_ht', data['sig_wave_ht'][i]),
        ('peak_wave_period', data['peak_wave_period'][i]),
        ('peak_wave_dir', data['peak_wave_dir'][i]),
        ('max_wave_ht', data['max_wave_ht'][i]),
        ('mean_wave_period', data['mean_wave_period'][i]),
        ('water_depth', data['water_depth'][i]),
        )

    return (global_atts, var_atts, var_data)

#
