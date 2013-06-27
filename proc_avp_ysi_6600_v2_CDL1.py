#!/usr/bin/env python
# Last modified:  Time-stamp: <2008-10-09 17:31:44 haines>
"""
how to parse data, and assert what data and info goes into
creating and updating monthly netcdf files

parse data from YSI 6600 V2-2 on an automated veritical profiler (avp)

parser : sample date and time, water_depth for each profile
         water temperature, conductivity, pressure (depth), salinity, pH, dissolved oxygen, turbidity, and chlorophyll
         raw data averaged to 10 cm bins

creator : lat, lon, z, time, water_depth, water_temp, cond, salin, ph, turb, chl, do 
updator : time, water_depth, water_temp, cond, salin, ph, turb, chl, do


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
    sample_dt_start = filt_datetime(fn)[0]

    # how many profiles in one file, count number of "Profile Time:" in lines
    nprof = 0
    for line in lines:
        m=re.search("Profile Time:", line)
        if m:
            nprof=nprof+1

    # remove first occurrence of blank line if within first 10-40 lines
    # and put it on the end to signal end of profile after last profile
    for i in range(len(lines[0:40])):
        if re.search("^ \r\n", lines[i]):
            # print str(i) + " " + lines[i] + " " + lines[i+1]
            blank_line = lines.pop(i)
            lines.append(blank_line)
    
    bin_size = sensor_info['bin_size'] # Bin Size (meters)
    nominal_depth = platform_info['water_depth']  # Mean sea level at station (meters) or nominal water depth
    z = numpy.arange(0, -1*nominal_depth, -1*bin_size, dtype=float)
    
    N = nprof
    nbins = len(z)

    if nbins != sensor_info['nbins']:
        print 'Number of bins computed from water_depth and bin_size ('+ \
              str(nbins)+') does not match config number ('+ \
              str(sensor_info['nbins'])+')'
    
    data = {
        'dt' : numpy.array(numpy.ones((N,), dtype=object)*numpy.nan),
        'time' : numpy.array(numpy.ones((N,), dtype=long)*numpy.nan),
        'z' : numpy.array(numpy.ones((nbins,), dtype=float)*numpy.nan),
        #
        'wd' : numpy.array(numpy.ones((N,), dtype=long)*numpy.nan),
        'wtemp' : numpy.array(numpy.ones((N,nbins), dtype=float)*numpy.nan),
        'cond' : numpy.array(numpy.ones((N,nbins), dtype=float)*numpy.nan),
        'salin' : numpy.array(numpy.ones((N,nbins), dtype=float)*numpy.nan),
        'turb' : numpy.array(numpy.ones((N,nbins), dtype=float)*numpy.nan),
        'ph' : numpy.array(numpy.ones((N,nbins), dtype=float)*numpy.nan),
        'chl' : numpy.array(numpy.ones((N,nbins), dtype=float)*numpy.nan),
        'do' : numpy.array(numpy.ones((N,nbins), dtype=float)*numpy.nan),
        }

    # current profile count
    i = 0 

    for line in lines:
        ysi = []
        # split line and parse float and integers
        sw = re.split('[\s/\:]*', line)
        for s in sw:
            m = re.search(REAL_RE_STR, s)
            if m:
                ysi.append(float(m.groups()[0]))

        if re.search("Profile Time:", line):
            HH=ysi[0]
            MM=ysi[1]
            SS=ysi[2]
        elif re.search("Profile Date:", line):
            mm=ysi[0]
            dd=ysi[1]
            yyyy=ysi[2]
        elif re.search("Profile Depth:", line):
            wd = ysi[0]/100.  # cm to meters
            sample_str = '%02d-%02d-%4d %02d:%02d:%02d' % (mm,dd,yyyy,HH,MM,SS)
            if  sensor_info['utc_offset']:
                sample_dt = scanf_datetime(sample_str, fmt='%m-%d-%Y %H:%M:%S') + \
                             timedelta(hours=sensor_info['utc_offset'])
            else:
                sample_dt = scanf_datetime(sample_str, fmt='%m-%d-%Y %H:%M:%S')

            # initialize for new profile at zero for averaging samples within each bin
            wtemp = numpy.zeros(nbins)
            cond = numpy.zeros(nbins)
            salin = numpy.zeros(nbins)
            turb = numpy.zeros(nbins)
            ph = numpy.zeros(nbins)
            chl = numpy.zeros(nbins)
            do = numpy.zeros(nbins)
            Ns = numpy.zeros(nbins) # count samples per bin for averaging
        elif len(ysi)==14:                                                                             
            # get sample datetime from data
            # sample_str = '%02d-%02d-%2d %02d:%02d:%02d' % tuple(ysi[0:6])
            # if  sensor_info['utc_offset']:
            #     sample_dt = scanf_datetime(sample_str, fmt='%m-%d-%Y %H:%M:%S') + \
            #                 timedelta(hours=sensor_info['utc_offset'])
            # else:
            # sample_dt = scanf_datetime(sample_str, fmt='%m-%d-%y %H:%M:%S')

            depth = -1*ysi[9] # depth (m, positive up)
            ibin = ((z)<=depth)*(depth<(z+bin_size))

            Ns[ibin] = Ns[ibin]+1
            wtemp[ibin] = wtemp[ibin]+ysi[6] # water temperature (C)
            cond[ibin] = cond[ibin]+ysi[7]   # conductivity (mS/cm)
            salin[ibin] = salin[ibin]+ysi[8] # salinity (ppt or PSU??)
            #
            ph[ibin] = ph[ibin]+ysi[10]      # ph
            turb[ibin] = turb[ibin]+ysi[11]  # turbidity (NTU)
            chl[ibin] = chl[ibin]+ysi[12]    # chlorophyll (ug/l)
            do[ibin] = do[ibin]+ysi[13]      # dissolved oxygen (mg/l)

        elif (len(ysi)==0):  # each profile separated by empty line
            # average summations by sample count per bin
            # where count is zero make it NaN so average is not divide by zero
            Ns[Ns==0]=numpy.nan*Ns[Ns==0]
            
            data['dt'][i] = sample_dt # sample datetime
            data['time'][i] = dt2es(sample_dt) # sample time in epoch seconds
            data['wd'][i] = wd
            data['z'] = z
            # divide by counts 
            data['wtemp'][i] =  wtemp/Ns
            data['cond'][i] = cond/Ns
            data['salin'][i] = salin/Ns
            data['turb'][i] = turb/Ns
            data['ph'][i] = ph/Ns
            data['chl'][i] = chl/Ns
            data['do'][i] = do/Ns
            
            i=i+1
            
        # if-elif
    # for line

    return data
 

def creator(platform_info, sensor_info, data):
    #
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
               'positive' : 'up',
               'units': 'm',
               'axis': 'Z',
               },
        # data variables
        'wtemp': {'short_name': 'wtemp',
                        'long_name': 'Water Temperature',
                        'standard_name': 'water_temperature',                          
                        'units': 'degrees Celsius',
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
        'depth': {'short_name': 'depth',
                  'long_name': 'Depth',
                  'standard_name': 'depth',                          
                  'units': 'm',
                  'reference':'zero at sea-surface',
                  'positive' : 'up',
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
        ('salin', NC.FLOAT, ('ntime',)),
        ('depth', NC.FLOAT, ('ntime',)),
        ('turb', NC.FLOAT, ('ntime',)),
        ('ph', NC.FLOAT, ('ntime',)),
        ('chl', NC.FLOAT, ('ntime',)),
        ('do', NC.FLOAT, ('ntime',)),
        )

    # subset data only to month being processed (see raw2proc.process())
    i = data['in']
    
    # var data 
    var_data = (
        ('lat',  platform_info['lat']),
        ('lon', platform_info['lon']),
        #
        ('time', data['time'][i]),
        ('z', 0),
        #
        ('wtemp', data['wtemp'][i]),
        ('cond', data['cond'][i]),
        ('salin', data['salin'][i]),
        ('depth', data['depth'][i]),
        ('turb', data['turb'][i]),
        ('ph', data['ph'][i]),
        ('chl', data['chl'][i]),
        ('do', data['do'][i]),
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
    #    'wtemp': {'max': max(data.u),
    #          'min': min(data.v),
    #          },
    #    'cond': {'max': max(data.u),
    #          'min': min(data.v),
    #          },
    #    }
    
    # subset data only to month being processed (see raw2proc.process())
    i = data['in']

    # data 
    var_data = (
        ('time', data['time'][i]),
        ('wtemp', data['wtemp'][i]),
        ('cond', data['cond'][i]),
        ('salin', data['salin'][i]),
        ('depth', data['depth'][i]),
        ('turb', data['turb'][i]),
        ('ph', data['ph'][i]),
        ('chl', data['chl'][i]),
        ('do', data['do'][i]),
        )

    return (global_atts, var_atts, var_data)
#
