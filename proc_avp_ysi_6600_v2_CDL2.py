#!/usr/bin/env python
# Last modified:  Time-stamp: <2011-02-24 11:00:27 haines>
"""
how to parse data, and assert what data and info goes into
creating and updating monthly netcdf files

parse data from YSI 6600 V2-2 on an automated veritical profiler (avp)

parser : date and time, water_depth for each profile

         sample time, sample depth, as cast measures water
         temperature, conductivity, salinity, pH, dissolved oxygen,
         turbidity, and chlorophyll
         

creator : lat, lon, z, stime, (time, water_depth), water_temp, cond,
          salin, ph, turb, chl, do

updator : z, stime, (time, water_depth), water_temp, cond, salin, ph,
          turb, chl, do

using fixed profiler CDL but modified to have raw data for each cast
along each column


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

2.  Use a ragged array to store each uniquely measured param at each
    time and depth but not gridded, so this uses fixed profiler CDL
    but modified to have raw data for each cast along each column.
    For plotting, the data will need to be grid at specified depth bins.

    Tony Whipple at IMS says 'The AVPs sample at one second intervals.
    Between the waves and the instrument descending from a spool of
    line with variable radius it works out to about 3-5 cm between
    observations on average.  When I process the data to make the
    images, I bin the data every 10 cm and take the average of however
    many observations fell within that bin.'

    """
    import numpy
    from datetime import datetime
    from time import strptime

    # get sample datetime from filename
    fn = sensor_info['fn']
    sample_dt_start = filt_datetime(fn)

    # how many profiles in one file, count number of "Profile Time:" in lines
    nprof = 0
    for line in lines:
        m=re.search("Profile Time:", line)
        if m:
            nprof=nprof+1

    # remove first occurrence of blank line if within first 40 lines
    for i in range(len(lines[0:40])):
       if re.search("^ \r\n", lines[i]):
           # print str(i) + " " + lines[i] + " " + lines[i+1]
           blank_line = lines.pop(i)
           # lines.append(blank_line)

    # ensure signal end of profile after last profile by appending a blank line to data file
    lines.append(' \r\n')
    
    # ensure blank line between profile casts
    for i, line in enumerate(lines):
        if re.search(r"Profile Time", line, re.IGNORECASE):
            if not re.search("^ \r\n", lines[i-1]):
                lines.insert(i, " \r\n")
    
    N = nprof
    nbins = sensor_info['nbins']

    data = {
        'dt' : numpy.array(numpy.ones((N,), dtype=object)*numpy.nan),
        'time' : numpy.array(numpy.ones((N,), dtype=long)*numpy.nan),
        'z' : numpy.array(numpy.ones((N,nbins), dtype=float)*numpy.nan),
        #
        'wd' : numpy.array(numpy.ones((N,), dtype=long)*numpy.nan),
        'wl' : numpy.array(numpy.ones((N,), dtype=long)*numpy.nan),
        # 'ysi_sn' : numpy.array(['' for i in range(N)] , dtype='|S20'), 
        # 'ysi_id' : numpy.array(['' for i in range(N)] , dtype='|S20'),
        #
        'stime' : numpy.array(numpy.ones((N,nbins), dtype=long)*numpy.nan),
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
    have_date = have_time = have_wd = have_location = have_head = False

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

        if re.search("Profile Time:", line):
            have_time = True
            HH=ysi[0]
            MM=ysi[1]
            SS=ysi[2]
        elif re.search("Profile Date:", line):
            have_date = True
            mm=ysi[0]
            dd=ysi[1]
            yyyy=ysi[2]
        elif re.search("Profile Depth:", line):
            have_wd = True
            wd = ysi[0]/100.  # cm to meters
            profile_str = '%02d-%02d-%4d %02d:%02d:%02d' % (mm,dd,yyyy,HH,MM,SS)
            if  sensor_info['utc_offset']:
                profile_dt = scanf_datetime(profile_str, fmt='%m-%d-%Y %H:%M:%S') + \
                             timedelta(hours=sensor_info['utc_offset'])
            else:
                profile_dt = scanf_datetime(profile_str, fmt='%m-%d-%Y %H:%M:%S')
        elif re.search("Profile Location:", line):
            have_location = True
            # Profile Location: Stones Bay Serial No: 00016B79, ID: AVP1_SERDP
            sw = re.findall(r'\w+:\s(\w+)*', line)
            # ysi_sn = sw[1]
            # ysi_id = sw[2]
            # initialize for new profile at zero for averaging samples within each bin
            wtemp = numpy.array(numpy.ones(nbins,), dtype=float)*numpy.nan
            depth =numpy.array(numpy.ones(nbins,), dtype=float)*numpy.nan
            cond = numpy.array(numpy.ones(nbins,), dtype=float)*numpy.nan
            salin = numpy.array(numpy.ones(nbins,), dtype=float)*numpy.nan
            turb = numpy.array(numpy.ones(nbins,), dtype=float)*numpy.nan
            ph = numpy.array(numpy.ones(nbins,), dtype=float)*numpy.nan
            chl = numpy.array(numpy.ones(nbins,), dtype=float)*numpy.nan
            do = numpy.array(numpy.ones(nbins,), dtype=float)*numpy.nan
            stime = numpy.array(numpy.ones(nbins,), dtype=long)*numpy.nan
            # keep track of number of samples in one profile so not to exceed nbins
            j = 0
            # have all the headers stuff
            head = numpy.array([have_date, have_time, have_wd, have_location])
            have_head = head.all()

        elif (len(ysi)==14 and have_head):
            if j>=nbins:
                print 'Sample number (' + str(j) + \
                      ') in profile exceeds maximum value ('+ \
                      str(nbins) + ') in config'
        
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
                if sensor_info['utc_offset']:
                    sample_dt = sample_dt + timedelta(hours=sensor_info['utc_offset'])
                #
                if j<nbins:
                    stime[j] = dt2es(sample_dt) # sample time
                    wtemp[j] = ysi[6] # water temperature (C)
                    cond[j] = ysi[7]  # conductivity (mS/cm)
                    salin[j] = ysi[8] # salinity (ppt or PSU??)
                    #
                    depth[j] = ysi[9] # depth (m, positive up)
                    #
                    ph[j] = ysi[10]   # ph
                    turb[j] = ysi[11] # turbidity (NTU)
                    chl[j] = ysi[12]  # chlorophyll (ug/l)
                    do[j] = ysi[13]   # dissolved oxygen (mg/l)
                    #
                    j = j+1
            else:
                print 'skipping line, ill-formed date ... ' + str(line)


        elif (len(ysi)==0 and have_head and i<N):  # each profile separated by empty line
            
            data['dt'][i] = profile_dt # profile datetime
            data['time'][i] = dt2es(profile_dt) # profile time in epoch seconds
            data['wd'][i] = -1.*wd
            data['wl'][i] = platform_info['mean_water_depth'] - (-1*wd)
            # data['ysi_sn'][i] = ysi_sn
            # data['ysi_id'][i] = ysi_id

            data['stime'][i] =  stime # sample time in epoch seconds
            data['z'][i] = -1.*depth

            data['wtemp'][i] =  wtemp
            data['cond'][i] = cond
            data['salin'][i] = salin
            data['turb'][i] = turb
            data['ph'][i] = ph
            data['chl'][i] = chl
            data['do'][i] = do
            
            i=i+1
            have_date = have_time = have_wd = have_location = False
        else:
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
               'long_name': 'Height',
               'standard_name': 'height',
               'reference':'zero at sea-surface',
               'positive' : 'up',
               'units': 'm',
               'axis': 'Z',
               },
        # data variables
        'stime' : {'short_name': 'stime',
                  'long_name': 'Time of Sample ',
                  'standard_name': 'time',
                  'units': 'seconds since 1970-1-1 00:00:00 -0', # UTC
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
        # 'ysi_id' : {'short_name':'ysi_id',
        #             'long_name':'Identification name of YSI Sonde',
        #             'standard_name': 'identification_name'
        #             },
        # 'ysi_sn' : {'short_name':'ysi_sn',
        #             'long_name':'Serial number of YSI Sonde',
        #             'standard_name': 'serial_number'
        #             },
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
        ('time', NC.UNLIMITED),
        ('lat', 1),
        ('lon', 1),
        ('z', sensor_info['nbins']),
        )
    
    # using tuple of tuples so order of initialization is maintained
    # using dict for attributes order of init not important
    # use dimension names not values
    # (varName, varType, (dimName1, [dimName2], ...))
    var_inits = (
        # coordinate variables
        ('time', NC.INT, ('time',)),
        ('lat', NC.FLOAT, ('lat',)),
        ('lon', NC.FLOAT, ('lon',)),
        ('z',  NC.FLOAT, ('time', 'z',)),
        # data variables
        ('wd', NC.FLOAT, ('time',)),
        ('wl', NC.FLOAT, ('time',)),
        # ('ysi_sn', NC.CHAR, ('time', 'nchar')),
        # ('ysi_id', NC.CHAR, ('time', 'nchar')),
        ('stime', NC.FLOAT, ('time', 'z')),        
        ('wtemp', NC.FLOAT, ('time', 'z')),
        ('cond', NC.FLOAT, ('time', 'z')),
        ('salin', NC.FLOAT, ('time', 'z')),
        ('turb', NC.FLOAT, ('time', 'z')),
        ('ph', NC.FLOAT, ('time', 'z')),
        ('chl', NC.FLOAT, ('time', 'z')),
        ('do', NC.FLOAT, ('time', 'z')),
        )

    # var data 
    var_data = (
        ('lat',  platform_info['lat']),
        ('lon', platform_info['lon']),
        ('time', data['time'][i]),
        ('wd', data['wd'][i]),
        ('wl', data['wl'][i]),
        # ('ysi_id', data['ysi_id'][i]),
        # ('ysi_sn', data['ysi_sn'][i]),
        ('stime', data['stime'][i]),
        ('z', data['z'][i]),
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
        ('wd', data['wd'][i]),
        ('wl', data['wl'][i]),
        # ('ysi_id', data['ysi_id'][i]),
        # ('ysi_sn', data['ysi_sn'][i]),
        ('stime', data['stime'][i]),
        ('z', data['z'][i]),
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
