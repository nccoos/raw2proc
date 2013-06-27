#!/usr/bin/env python
# Last modified:  Time-stamp: <2010-12-09 16:13:37 haines>
"""
how to parse data, and assert what data and info goes into
creating and updating monthly netcdf files

RDI/Wavesmon processed adcp current profile data

parser : sample date and time, currents, water temperature, pressure and water_depth

creator : lat, lon, z, time, ens, u, v, w, water_depth, water_temp (at tranducer depth), pressure
updator : time, ens, u, v, w, water_depth, water_temp (at tranducer depth), pressure


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

import seawater

now_dt = datetime.utcnow()
now_dt.replace(microsecond=0)

def parser(platform_info, sensor_info, lines):
    """
    parse and assign ocean profile current data from Nortek AWAC ADCP Data

    Notes
    -----
    1. This parser requires date/time be parsed from .wap for each to
    get sig_wave_ht for determining depth of each bin and surface mask
    and check time same as in .wpa file. 

    2. multiple profiles in one file separated by header w/time,
       pitch, roll, heading, ducer pressure, bottom temp, top bin#
       bottom bin# (??).  The profile data is several lines one for
       each bin.
    
    MM DD YYYY HH MM SS  ERR STATUS BATT SNDSPD HDG  PITCH  ROLL  PRESS   WTEMP    ??  ?? TBIN BBIN
    07 31 2008 23 54 00    0   48  18.2 1525.8 270.1  -2.4   0.2  10.503  21.64     0     0 3  34
       1    0.9    0.071   24.04    0.029    0.065   -0.058 123 126 124
       2    1.4    0.089  342.38   -0.027    0.085   -0.057 110 111 113
       3    1.9    0.065  310.03   -0.050    0.042   -0.063 102 104 104
       4    2.4    0.063   46.93    0.046    0.043   -0.045  93  95  99
       5    2.9    0.049  355.33   -0.004    0.049   -0.047  87  89  92
         ...
     NBIN  DEPTH   SPEED    DIR       U         V       W    E1? E2? E3?
       32   16.4    0.184  331.76   -0.087    0.162   -0.162  26  25  27
       33   16.9    0.137  288.70   -0.130    0.044   -0.181  26  24  26
       34   17.4    0.070   32.78    0.038    0.059   -0.248  25  25  26

    3. not sure if depth column is hab or down from surface? 


    """

    # get sample datetime from filename
    fn = sensor_info['fn']
    sample_dt_start = filt_datetime(fn)

    nbins = sensor_info['nbins']  # Number of bins in data
    nbursts = len(lines)/(nbins+1)

    data = {
        'dt' : numpy.array(numpy.ones((nbursts,), dtype=object)*numpy.nan),
        'time' : numpy.array(numpy.ones((nbursts,), dtype=long)*numpy.nan),
        'z' : numpy.array(numpy.ones((nbins,), dtype=float)*numpy.nan),
        'u' : numpy.array(numpy.ones((nbursts,nbins), dtype=float)*numpy.nan),
        'v' : numpy.array(numpy.ones((nbursts,nbins), dtype=float)*numpy.nan),
        'w' : numpy.array(numpy.ones((nbursts,nbins), dtype=float)*numpy.nan),
        'e1' : numpy.array(numpy.ones((nbursts,nbins), dtype=int)*numpy.nan),
        'e2' : numpy.array(numpy.ones((nbursts,nbins), dtype=int)*numpy.nan),
        'e3' : numpy.array(numpy.ones((nbursts,nbins), dtype=int)*numpy.nan),
        'wd' : numpy.array(numpy.ones((nbursts), dtype=float)*numpy.nan),
        'wl' : numpy.array(numpy.ones((nbursts), dtype=float)*numpy.nan),
        'water_temp' : numpy.array(numpy.ones((nbursts), dtype=float)*numpy.nan),
        'pressure' : numpy.array(numpy.ones((nbursts), dtype=float)*numpy.nan),
        }

    # these items can also be teased out of raw adcp but for now get from config file
    th = sensor_info['transducer_ht']  # Transducer height above bottom (meters)
    bh = sensor_info['blanking_ht']    # Blanking height above Transducer (meters)
    bin_size = sensor_info['bin_size'] # Bin Size (meters)
    
    # compute height for each bin above the bottom
    bins = numpy.arange(1,nbins+1)
    # bin_habs = (bins*bin_size+bin_size/2)+th+bh
    bin_habs = (bins*bin_size+bin_size/2)+th+bh

    # added by SH -- 15 Oct 2008
    # raw2proc:ticket:27 adjust bin_habs along beam to nadir
    # Nortek awac beam angle is fixed at 25 deg
    # adjustment is cos(25 deg) (which is  approx .90*height)
    # -------------------
    # bin_habs =  (bin_habs*numpy.cos(25.*numpy.pi/180))
    # -------------------
    # commented out by SH -- 18 Aug 2010
    # This does not apply to habs provided in .wpa.  They
    # are adjusted for beam angle in ascii output.
    iaboveblank = bin_habs > th+bh+(bin_size)

    # current profile count
    i = 0 

    wpa = []
    for line in lines:
        wpa = []
        # split line and parse float and integers
        sw = re.split(' ', line)
        for s in sw:
            m = re.search(REAL_RE_STR, s)
            if m:
                wpa.append(float(m.groups()[0]))

        if len(wpa)==19:                                                                             
            # get sample datetime from data
            sample_str = '%02d-%02d-%4d %02d:%02d:%02d' % tuple(wpa[0:6])
            if  sensor_info['utc_offset']:
                sample_dt = scanf_datetime(sample_str, fmt='%m-%d-%Y %H:%M:%S') + \
                            timedelta(hours=sensor_info['utc_offset'])
            else:
                sample_dt = scanf_datetime(sample_str, fmt='%m-%d-%Y %H:%M:%S')
            
            # these items can also be teased out of raw adcp but for now get from config file
            # th = sensor_info['transducer_ht']  # Transducer height above bottom (meters)
            
            error_code = int(wpa[6])
            status_code = int(wpa[7])
            battery_voltage = wpa[8] # volts
            sound_speed = wpa[9]     # m/s
            heading = wpa[10]        # deg
            pitch = wpa[11]          # deg
            roll = wpa[12]           # deg
            
            pressure = wpa[13]       # dbar
            # pressure (dbar) converted to water depth
            wd = th + seawater.depth(pressure, platform_info['lat']) # m
            temperature = wpa[14]       # deg C

            start_bin = int(wpa[17])     # first good bin from transducer (?)
            wpa_nbins = int(wpa[18])     # Number of bins
            # check this is same as in sensor_info

            # initialize for new profile
            hab = numpy.ones(nbins)*numpy.nan
            spd = numpy.ones(nbins)*numpy.nan
            dir = numpy.ones(nbins)*numpy.nan
            u = numpy.ones(nbins)*numpy.nan
            v = numpy.ones(nbins)*numpy.nan
            w = numpy.ones(nbins)*numpy.nan
            e1 = numpy.array(numpy.ones((nbins), dtype=int)*numpy.nan)
            e2 = numpy.array(numpy.ones((nbins), dtype=int)*numpy.nan)
            e3 = numpy.array(numpy.ones((nbins), dtype=int)*numpy.nan)

        elif len(wpa)==10:
            # current profile data at  each bin
            bin_number = wpa[0]
            j = wpa[0]-1
            # print j
            hab[j] = wpa[1]
            
            spd[j] = wpa[2] # m/s
            dir[j] = wpa[3] # deg N

            u[j] = wpa[4] # m/s
            v[j] = wpa[5] # m/s
            w[j] = wpa[6] # m/s

            e1[j] = int(wpa[7]) # echo dB ??
            e2[j] = int(wpa[8]) # 
            e3[j] = int(wpa[9]) #

            # ibad = (current_spd==-32768) | (current_dir==-32768)
            # current_spd[ibad] = numpy.nan
            # current_dir[ibad] = numpy.nan

            # if done reading profile, just read data for last bin
            if bin_number==nbins:
                # compute water mask
                # if positive is up, in water is less than zero depth
                bin_depths =  (bin_habs)-(wd)
                iwater = bin_depths+bin_size/2 < 0
                iwater = iwater*iaboveblank
                
                # use nominal water depth (MSL) averaged from full pressure record
                #  this should be checked/recalulated every so often
                z = bin_habs+platform_info['mean_water_depth']
                
                data['dt'][i] = sample_dt # sample datetime
                data['time'][i] = dt2es(sample_dt) # sample time in epoch seconds
                data['z'] =  z
                data['wd'][i] = -1*wd
                data['wl'][i] = platform_info['mean_water_depth'] - (-1*wd)
                data['water_temp'][i] = temperature
                data['pressure'][i] = pressure
                
                data['u'][i][iwater] =  u[iwater]
                data['v'][i][iwater] =  v[iwater]
                data['w'][i][iwater] =  w[iwater]

                data['e1'][i] =  e1
                data['e2'][i] =  e2
                data['e3'][i] =  e3

                # ready for next burst
                i = i+1
            # if j+1==nbins
        # if len(wpa)==19 elif ==10
    # for line

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
               'reference':'zero at mean-sea-level',
               'positive' : 'up',
               'units': 'm',
               'axis': 'Z',
               },
        # data variables
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
        'w': {'short_name' : 'w',
              'long_name': 'Vertical Component of Current',
              'standard_name': 'upward_current',                          
              'units': 'm s-1',
              'reference': 'clockwise from True North',
              },
        'e1': {'short_name' : 'e1',
              'long_name': 'Echo Beam 1 (??)',
              'standard_name': 'beam_echo',
              'units': 'dB',
              },
        'e2': {'short_name' : 'e2',
              'long_name': 'Echo Beam 2 (??)',
              'standard_name': 'beam_echo',
              'units': 'dB',
              },
        'e3': {'short_name' : 'e3',
              'long_name': 'Echo Beam 3 (??)',
              'standard_name': 'beam_echo',
              'units': 'dB',
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
        'pressure': {'short_name': 'p',
                     'long_name': 'Pressure',
                     'standard_name': 'pressure',                          
                     'units': 'dbar',
                     },
        'water_temp': {'short_name': 'wtemp',
                        'long_name': 'Water Temperature at Transducer',
                        'standard_name': 'water_temperature',                          
                        'units': 'deg_C',
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
        ('u', NC.FLOAT, ('ntime', 'nz')),
        ('v', NC.FLOAT, ('ntime', 'nz')),
        ('w', NC.FLOAT, ('ntime', 'nz')),
        ('e1', NC.INT, ('ntime', 'nz')),
        ('e2', NC.INT, ('ntime', 'nz')),
        ('e3', NC.INT, ('ntime', 'nz')),
        ('wd', NC.FLOAT, ('ntime',)),
        ('wl', NC.FLOAT, ('ntime',)),
        ('pressure', NC.FLOAT, ('ntime',)),
        ('water_temp', NC.FLOAT, ('ntime',)),
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
        ('u', data['u'][i]),
        ('v', data['v'][i]),
        ('w', data['w'][i]),
        ('e1', data['e1'][i]),
        ('e2', data['e2'][i]),
        ('e3', data['e3'][i]),
        ('wd', data['wd'][i]),
        ('wl', data['wl'][i]),
        ('pressure', data['pressure'][i]),
        ('water_temp', data['water_temp'][i]),
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
        ('w', data['w'][i]),
        ('e1', data['e1'][i]),
        ('e2', data['e2'][i]),
        ('e3', data['e3'][i]),
        ('wd', data['wd'][i]),
        ('wl', data['wl'][i]),
        ('pressure', data['pressure'][i]),
        ('water_temp', data['water_temp'][i]),
        )

    return (global_atts, var_atts, var_data)
#
