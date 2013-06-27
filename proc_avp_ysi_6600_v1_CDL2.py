#!/usr/bin/env python
# Last modified:  Time-stamp: <2010-12-09 16:15:11 haines>
"""
how to parse data, and assert what data and info goes into
creating and updating monthly netcdf files

parse data from YSI 6600 V1 on an automated veritical profiler (avp)

parser : date and time, water_depth for each profile

         sample time, sample depth, as cast measures water
         temperature, conductivity, salinity, dissolved oxygen,
         turbidity, and chlorophyll (no pH)
         

creator : lat, lon, z, stime, (time, water_depth), water_temp, cond,
          salin, turb, chl, do

updator : z, stime, (time, water_depth), water_temp, cond, salin,
          turb, chl, do

using fixed profiler CDL but modified to have raw data for each cast
along each column


Examples
--------

>> (parse, create, update) = load_processors('proc_avp_ysi_6600_v1')
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
    1. Column Format YSI 6600 V1 has no pH

    temp, cond,   salin,  DO,    depth, turb,  chl
    (C), (mS/cm), (ppt), (ug/l), (m),   (NTU), (ug/l)


(from Aug 2005 to Sep 03 2008)
    profile time: 00:00:56
    profile date: 01/31/2006
    profile location: P180, Instrument Serial No: 0001119E
    01/31/06 00:01:31 10.99  7.501   4.16  13.22   0.516     6.0  11.5
    01/31/06 00:01:32 11.00  7.463   4.13  13.22   0.526     6.0  11.4
    01/31/06 00:01:33 11.00  7.442   4.12  13.22   0.538     6.0  11.4
    01/31/06 00:01:34 11.00  7.496   4.15  13.11   0.556     6.0  11.3
(no data from Sep 03 to 30, 2008)
(from Sep 30 2008 to now, still YSI 6600 v1, just header change)
    Profile Time: 11:38:00
    Profile Date: 01/06/2009
    Profile Depth: 380.0 cm
    Profile Location: Hampton Shoal Serial No: 000109DD, ID: Delta
    01/06/09 11:38:44 11.16  14.59   8.49  17.86   0.171     4.5  50.4
    01/06/09 11:38:45 11.16  14.59   8.49  17.86   0.190     4.5  51.8
    01/06/09 11:38:46 11.16  14.59   8.49  17.88   0.220     4.6  53.0
    01/06/09 11:38:47 11.16  14.59   8.49  17.88   0.257     4.6  53.9
    01/06/09 11:38:48 11.16  14.59   8.49  17.88   0.448     4.6  54.3

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
        m=re.search("Profile Time:", line, re.IGNORECASE)
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
        # 'ysi_sn' : numpy.array(['' for i in range(N)] , dtype='|S20'), 
        # 'ysi_id' : numpy.array(['' for i in range(N)] , dtype='|S20'),
        #
        'stime' : numpy.array(numpy.ones((N,nbins), dtype=long)*numpy.nan),
        'wtemp' : numpy.array(numpy.ones((N,nbins), dtype=float)*numpy.nan),
        'cond' : numpy.array(numpy.ones((N,nbins), dtype=float)*numpy.nan),
        'salin' : numpy.array(numpy.ones((N,nbins), dtype=float)*numpy.nan),
        'turb' : numpy.array(numpy.ones((N,nbins), dtype=float)*numpy.nan),
        'chl' : numpy.array(numpy.ones((N,nbins), dtype=float)*numpy.nan),
        'do' : numpy.array(numpy.ones((N,nbins), dtype=float)*numpy.nan),
        }

    # current profile count
    i = 0
    have_date = have_time = have_location = have_head = False
    verbose = False

    for line in lines:
        # if line has weird ascii chars -- skip it and iterate to next line
        if re.search(r"[\x1a]", line):
            if verbose:
                print 'skipping bad data line ... ' + str(line)
            continue
            
        ysi = []
        # split line and parse float and integers
        sw = re.split('[\s/\:]*', line)
        for s in sw:
            m = re.search(REAL_RE_STR, s)
            if m:
                ysi.append(float(m.groups()[0]))

        if re.search("Profile Time:", line, re.IGNORECASE):
            have_time = True
            HH=ysi[0]
            MM=ysi[1]
            SS=ysi[2]
        elif re.search("Profile Date:", line, re.IGNORECASE):
            have_date = True
            mm=ysi[0]
            dd=ysi[1]
            yyyy=ysi[2]

            profile_str = '%02d-%02d-%4d %02d:%02d:%02d' % (mm,dd,yyyy,HH,MM,SS)
            if  sensor_info['utc_offset']:
                profile_dt = scanf_datetime(profile_str, fmt='%m-%d-%Y %H:%M:%S') + \
                             timedelta(hours=sensor_info['utc_offset'])
            else:
                profile_dt = scanf_datetime(profile_str, fmt='%m-%d-%Y %H:%M:%S')
        elif re.search("Profile Location:", line):
            have_location = True
            # profile location: P180, Instrument Serial No: 0001119E
            # Profile Location: Hampton Shoal Serial No: 000109DD, ID: Delta
            sw = re.findall(r'\w+:\s(\w+)*', line)
            # ysi_sn = sw[1]
            # ysi_id = sw[2]
                
            # initialize for new profile at zero for averaging samples within each bin
            wtemp = numpy.array(numpy.ones(nbins,), dtype=float)*numpy.nan
            depth =numpy.array(numpy.ones(nbins,), dtype=float)*numpy.nan
            cond = numpy.array(numpy.ones(nbins,), dtype=float)*numpy.nan
            salin = numpy.array(numpy.ones(nbins,), dtype=float)*numpy.nan
            turb = numpy.array(numpy.ones(nbins,), dtype=float)*numpy.nan
            chl = numpy.array(numpy.ones(nbins,), dtype=float)*numpy.nan
            do = numpy.array(numpy.ones(nbins,), dtype=float)*numpy.nan
            stime = numpy.array(numpy.ones(nbins,), dtype=long)*numpy.nan
            # keep track of number of samples in one profile so not to exceed nbins
            j = 0
            # have all the headers stuff
            head = numpy.array([have_date, have_time, have_location])
            have_head = head.all()

        elif re.search("Error", line):
            # ignore this line
            if verbose:
                print 'skipping bad data line ... ' + str(line)
            continue

        elif (len(ysi)==13 and have_head):
            if j>=nbins:
                print 'Sample number (' + str(j) + \
                      ') in profile exceeds maximum value ('+ \
                      str(nbins) + ') in config'
        
            # get sample datetime from data
            sample_str = '%02d-%02d-%02d %02d:%02d:%02d' % tuple(ysi[0:6])
            try:
                if  sensor_info['utc_offset']:
                    sample_dt = scanf_datetime(sample_str, fmt='%m-%d-%y %H:%M:%S') + \
                                timedelta(hours=sensor_info['utc_offset'])
                else:
                    sample_dt = scanf_datetime(sample_str, fmt='%m-%d-%y %H:%M:%S')
            except TypeError:
                if verbose:
                    print 'bad time stamp, skipping data line .... ' + str(line)
                continue
                

            if j<nbins:
                stime[j] = dt2es(sample_dt) # sample time
                wtemp[j] = ysi[6] # water temperature (C)
                cond[j] = ysi[7]  # conductivity (mS/cm)
                salin[j] = ysi[8] # salinity (ppt or PSU??)
                do[j] = ysi[9]   # dissolved oxygen (mg/l)
                #
                depth[j] = ysi[10] # depth (m, positive up)
                #
                turb[j] = ysi[11] # turbidity (NTU)
                chl[j] = ysi[12]  # chlorophyll (ug/l)

            j = j+1

        elif (len(ysi)==0 and have_head and i<N):  # each profile separated by empty line

            data['dt'][i] = profile_dt # profile datetime
            data['time'][i] = dt2es(profile_dt) # profile time in epoch seconds
            # data['ysi_sn'][i] = ysi_sn
            # data['ysi_id'][i] = ysi_id
            #
            data['stime'][i] =  stime # sample time in epoch seconds
            data['z'][i] = -1.*depth
            #
            data['wtemp'][i] =  wtemp
            data['cond'][i] = cond
            data['salin'][i] = salin
            data['turb'][i] = turb
            data['chl'][i] = chl
            data['do'][i] = do
            
            i=i+1
            have_date = have_time = have_wd = have_location = False
        else:
            if verbose:
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
        # ('ysi_sn', NC.CHAR, ('time', 'nchar')),
        # ('ysi_id', NC.CHAR, ('time', 'nchar')),
        ('stime', NC.FLOAT, ('time', 'z')),        
        ('wtemp', NC.FLOAT, ('time', 'z')),
        ('cond', NC.FLOAT, ('time', 'z')),
        ('salin', NC.FLOAT, ('time', 'z')),
        ('turb', NC.FLOAT, ('time', 'z')),
        ('chl', NC.FLOAT, ('time', 'z')),
        ('do', NC.FLOAT, ('time', 'z')),
        )

    # var data 
    var_data = (
        ('lat',  platform_info['lat']),
        ('lon', platform_info['lon']),
        ('time', data['time'][i]),
        # ('ysi_id', data['ysi_id'][i]),
        # ('ysi_sn', data['ysi_sn'][i]),
        ('stime', data['stime'][i]),
        ('z', data['z'][i]),
        #
        ('wtemp', data['wtemp'][i]),
        ('cond', data['cond'][i]),
        ('salin', data['salin'][i]),
        ('turb', data['turb'][i]),
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
        # ('ysi_id', data['ysi_id'][i]),
        # ('ysi_sn', data['ysi_sn'][i]),
        ('stime', data['stime'][i]),
        ('z', data['z'][i]),
        #
        ('wtemp', data['wtemp'][i]),
        ('cond', data['cond'][i]),
        ('salin', data['salin'][i]),
        ('turb', data['turb'][i]),
        ('chl', data['chl'][i]),
        ('do', data['do'][i]),
        )

    return (global_atts, var_atts, var_data)
#
