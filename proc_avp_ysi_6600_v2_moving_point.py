#!/usr/bin/env python
# Last modified:  Time-stamp: <2011-05-05 14:43:47 haines>
"""
how to parse data, and assert what data and info goes into
creating and updating monthly netcdf files

parse data from YSI 6600 V2-2 on an automated veritical profiler (avp)

parser : date and time, water_depth for each profile

         sample time, sample depth, as cast measures water
         temperature, conductivity, salinity, pH, dissolved oxygen,
         turbidity, and chlorophyll
         

creator : lat, lon, z, time, water_depth, water_temp, cond,
          salin, ph, turb, chl, do

updator : z, time, water_depth, water_temp, cond, salin, ph,
          turb, chl, do

using moving point CDL 


Examples
--------

>> (parse, create, update) = load_processors('proc_avp_ysi_6600_v2')
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
    parse Automated Vertical Profile Station (AVP) Water Quality Data

    month, day, year, hour, min, sec, temp (deg. C), conductivity
    (mS/cm), salinity (ppt or PSU), depth (meters), pH, turbidity (NTU),
    chlorophyll (micrograms per liter), DO (micrograms per liter)

    Notes
    -----
    1. Column Format

    temp, cond, salin, depth, pH, turb, chl, DO
    (C), (mS/cm), (ppt), (m), pH, (NTU), (ug/l), (ug/l)

    Profile Time: 00:30:00
    Profile Date: 08/18/2008
    Profile Depth: 255.0 cm
    Profile Location: Stones Bay Serial No: 00016B79, ID: AVP1_SERDP
    08/18/08 00:30:06 26.94  41.87  26.81   0.134  8.00     3.4   4.5   6.60
    08/18/08 00:30:07 26.94  41.87  26.81   0.143  8.00     3.4   4.8   6.59
    08/18/08 00:30:08 26.94  41.87  26.81   0.160  8.00     3.4   4.8   6.62
    08/18/08 00:30:09 26.94  41.87  26.81   0.183  8.00     3.4   4.8   6.66


    """
    import numpy
    from datetime import datetime
    from time import strptime

    # get sample datetime from filename
    fn = sensor_info['fn']
    sample_dt_start = filt_datetime(fn)

    # how many samples
    nsamp = 0
    for line in lines:
        # if line has weird ascii chars -- skip it and iterate to next line
        if re.search(r"[\x1a]", line):
            # print 'skipping bad data line ... ' + str(line)
            continue
        m=re.search("^\d{2}\/\d{2}\/\d{2}", line)
        if m:
            nsamp=nsamp+1

    N = nsamp

    data = {
        'dt' : numpy.array(numpy.ones((N,), dtype=object)*numpy.nan),
        'time' : numpy.array(numpy.ones((N,), dtype=long)*numpy.nan),
        'z' : numpy.array(numpy.ones((N,), dtype=long)*numpy.nan),
        'wd' : numpy.array(numpy.ones((N,), dtype=long)*numpy.nan),
        'wl' : numpy.array(numpy.ones((N,), dtype=long)*numpy.nan),
        'batt' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'wtemp' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'cond' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'salin' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'turb' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'ph' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'chl' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        'do' : numpy.array(numpy.ones((N,), dtype=float)*numpy.nan),
        }

    # setting all dates to this old data so eliminated for this month
    for i in range(N):
        data['dt'][i] = datetime(1970,1,1)

    # sample count
    i = 0

    for line in lines:
        # if line has weird ascii chars -- skip it and iterate to next line
        if re.search(r"[\x1a]", line):
            # print 'skipping bad data line ... ' + str(line)
            continue

        ysi = []
        # split line and parse float and integers
        sw = re.split('[\s/\:]*', line)
        for s in sw:
            m = re.search(REAL_RE_STR, s)
            if m:
                ysi.append(float(m.groups()[0]))

        if re.search("Profile Depth:", line) and i<N:
            sw = re.match("Profile Depth: " + REAL_RE_STR + "(\\w+)", line)
            if (ysi[0] is not None) and (sw is not None):
                unit_str = sw.groups()[-1]
                if unit_str is not None:
                    (wd, unit_str) = udconvert(ysi[0], unit_str, 'm') # to meters
                else:
                    wd = numpy.nan
            else:
                wd = numpy.nan

            wl = platform_info['mean_water_depth'] - (-1*wd)
            data['wl'][i] = wl
            data['wd'][i] = -1*wd

        if re.search("Voltage", line) and i<N:
            batt = ysi[0]  # volts
            data['batt'][i] = batt

        if re.search("Profile Location:", line):
            # Profile Location: Stones Bay Serial No: 00016B79, ID: AVP1_SERDP
            sw = re.findall(r'\w+:\s(\w+)*', line)
            # ysi_sn = sw[1]
            # ysi_id = sw[2]

        if re.search("^\d{2}\/\d{2}\/\d{2}", line) and len(ysi)==14 and i<N:
            # get sample datetime from data
            sample_str = '%02d-%02d-%02d %02d:%02d:%02d' % tuple(ysi[0:6])

            # month, day, year
            try:
                sample_dt = scanf_datetime(sample_str, fmt='%m-%d-%y %H:%M:%S')
            except ValueError:
                # day, month, year (month and day switched in some cases)
                try:
                    sample_dt = scanf_datetime(sample_str, fmt='%d-%m-%y %H:%M:%S')
                except:
                    sample_dt = datetime(1970,1,1)

            if sample_dt is not None:
                wtemp = ysi[6] # water temperature (C)
                cond  = ysi[7] # conductivity (mS/cm)
                salin = ysi[8] # salinity (ppt or PSU??)
                depth = ysi[9] # depth (m) 
                #
                ph = ysi[10]   # ph
                turb = ysi[11] # turbidity (NTU)
                chl = ysi[12]  # chlorophyll (ug/l)
                do = ysi[13]   # dissolved oxygen (ug/l)
            
                data['dt'][i] = sample_dt # sample datetime
                data['time'][i] = dt2es(sample_dt) # sample time in epoch seconds
                #
                data['wtemp'][i] =  wtemp
                data['cond'][i] = cond
                data['salin'][i] = salin
                data['z'][i] = -1*depth # relative to surface

                data['turb'][i] = turb
                data['ph'][i] = ph
                data['chl'][i] = chl
                data['do'][i] = do            
                i=i+1
                
            else:
                print 'skipping line, ill-formed date ... ' + str(line)

        elif (len(ysi)>=6 and len(ysi)<14):
            print 'skipping bad data line ... ' + str(line)

        # if-elif
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
        'institution' : 'Unversity of North Carolina at Chapel Hill (UNC-CH)',
        'institution_url' : 'http://nccoos.unc.edu',
        'institution_dods_url' : 'http://nccoos.unc.edu',
        'metadata_url' : 'http://nccoos.unc.edu',
        'references' : 'http://nccoos.unc.edu',
        'contact' : 'Sara Haines (haines@email.unc.edu)',
        # 
        'source' : 'fixed-automated-profiler observation',
        'history' : 'raw2proc using ' + sensor_info['process_module'],
        'comment' : 'File created using pycdf'+pycdfVersion()+' and numpy '+pycdfArrayPkg(),
        # conventions
        'Conventions' : 'CF-1.0; SEACOOS-CDL-v2.0',
        # SEACOOS CDL codes
        'format_category_code' : 'fixed-profiler-ragged',
        'institution_code' : platform_info['institution'],
        'platform_code' : platform_info['id'],
        'package_code' : sensor_info['id'],
        # institution specific
        'project' : 'North Carolina Coastal Ocean Observing System (NCCOOS)',
        'project_url' : 'http://nccoos.unc.edu',
        # timeframe of data contained in file yyyy-mm-dd HH:MM:SS
        # first date in monthly file
        'start_date' : dt[0].strftime("%Y-%m-%d %H:%M:%S"),
        # last date in monthly file
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
                  'long_name': 'Time of Profile',
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
               'long_name': 'z',
               'standard_name': 'z',
               'reference':'zero is surface',
               'positive' : 'up',
               'units': 'm',
               'axis': 'Z',
               },
        # data variables
        'batt': {'short_name': 'batt',
               'long_name': 'Battery',
               'standard_name': 'battery_voltage',
               'units': 'volts',
               },
        'wd': {'short_name': 'wd',
               'long_name': 'Water Depth',
               'standard_name': 'water_depth',                          
               'reference' : 'zero at sea-surface',
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
        'wtemp': {'short_name': 'wtemp',
                        'long_name': 'Water Temperature',
                        'standard_name': 'water_temperature',                          
                        'units': 'degrees_Celsius',
                        },
        'cond': {'short_name': 'cond',
                        'long_name': 'Conductivity',
                        'standard_name': 'conductivity',                          
                        'units': 'mS cm-1',
                        },
        'salin': {'short_name': 'salin',
                        'long_name': 'Salinity',
                        'standard_name': 'salinity',                          
                        'units': 'PSU',
                        },
        'turb': {'short_name': 'turb',
                        'long_name': 'Turbidity',
                        'standard_name': 'turbidity',                          
                        'units': 'NTU',
                        },
        'ph': {'short_name': 'ph',
                        'long_name': 'pH',
                        'standard_name': 'ph',                          
                        'units': '',
                        },
        'chl': {'short_name': 'chl',
                        'long_name': 'Chlorophyll',
                        'standard_name': 'chlorophyll',                          
                        'units': 'ug l-1',
                        },
        'do': {'short_name': 'do',
                        'long_name': 'Dissolved Oxygen',
                        'standard_name': 'dissolved_oxygen',                          
                        'units': 'mg l-1',
                        },
        }

    # dimension names use tuple so order of initialization is maintained
    dim_inits = (
        ('ntime', NC.UNLIMITED),
        ('nlat', 1),
        ('nlon', 1),
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
        ('z',  NC.FLOAT, ('ntime',)),
        # data variables
        ('batt', NC.FLOAT, ('ntime',)),
        ('wd', NC.FLOAT, ('ntime',)),
        ('wl', NC.FLOAT, ('ntime',)),
        #
        ('wtemp', NC.FLOAT, ('ntime',)),
        ('cond', NC.FLOAT, ('ntime',)),
        ('salin', NC.FLOAT, ('ntime',)),
        ('turb', NC.FLOAT, ('ntime',)),
        ('ph', NC.FLOAT, ('ntime',)),
        ('chl', NC.FLOAT, ('ntime',)),
        ('do', NC.FLOAT, ('ntime',)),
        )

    # var data 
    var_data = (
        ('lat',  platform_info['lat']),
        ('lon', platform_info['lon']),
        ('time', data['time'][i]),
        ('z', data['z'][i]),
        #
        ('batt', data['batt'][i]),
        ('wd', data['wd'][i]),
        ('wl', data['wl'][i]),
        #
        ('wtemp', data['wtemp'][i]),
        ('cond', data['cond'][i]),
        ('salin', data['salin'][i]),
        ('turb', data['turb'][i]),
        ('ph', data['ph'][i]),
        ('chl', data['chl'][i]),
        ('do', data['do'][i]),
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
        ('z', data['z'][i]),
        #
        ('batt', data['batt'][i]),
        ('wd', data['wd'][i]),
        ('wl', data['wl'][i]),
        #
        ('wtemp', data['wtemp'][i]),
        ('cond', data['cond'][i]),
        ('salin', data['salin'][i]),
        ('turb', data['turb'][i]),
        ('ph', data['ph'][i]),
        ('chl', data['chl'][i]),
        ('do', data['do'][i]),
        )

    return (global_atts, var_atts, var_data)
#
