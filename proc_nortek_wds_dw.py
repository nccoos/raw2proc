#!/usr/bin/env python
# Last modified:  Time-stamp: <2010-12-09 16:13:56 haines>
"""
how to parse data, and assert what data and info goes into
creating and updating monthly netcdf files

Nortek/AWAC processed adcp 2-D power spectrum (wds) as function of
frequency and direction

parser : sample date and time and pressure from .wap,
         energy spectrum m^2/Hz from .was,
         normalized energy/deg from .wds

         based on George Voulgaris' matlab script (version 8, Feb 14, 2005,
         polar_waves_cur_rdi.m) and additional parameters.
creator : lat, lon, z, time, freq, dir, Sxx(time, freq, dir), Sf(time, freq),
          Stheta(time, dir), Stheta_swell(time, dir), Stheta_wind(time, dir),
          Hs, Hs_swell, Hs_wind,
          Tp, Tp_swell, Tp_wind, Tm, Tm_swell, Tm_wind,
          Dp, Dp_swell, Dp_wind, Dm, Dm_swell, Dm_wind,
          
updater : time, Sxx(time, freq, dir), Sf(time, freq),
          Stheta(time, dir), Stheta_swell(time, dir), Stheta_wind(time, dir),
          Hs, Hs_swell, Hs_wind,
          Tp, Tp_swell, Tp_wind, Tm, Tm_swell, Tm_wind,
          Dp, Dp_swell, Dp_wind, Dm, Dm_swell, Dm_wind,

          check that freq and dir have not changed from what is in current
          NetCDF file

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
    parse and assign wave spectra data from RDI ADCP Dspec
    and compute wave statistics and parameters

    Notes
    -----
    1. adapted from polar_waves_cur_rdi.m  (Version 8 - February 14, 2005)
       by George Voulgaris
       Coastal Processes & Sediment Dynamics Lab
       Department of Geological Sciences
       University of South Carolina, Columbia, SC 29205
       Email: gvoulgaris@geol.sc.edu
    2. This parser requires date/time be parsed from .wap for each
    spectum sample in .wds, strip .wds on input filename and load and
    parse .wap here.  If .wap with same name not available, then use sample
    per hour starting at time parsed from filename.  
    
    3. The .wds contains several bursts of full directional wave
    spectrum. One for each hour in .wap. Each directional burst is
    formatted in .wds file as each row is a one frequency, default
    [0.02:0.01:0.99] or [0.02:0.01:0.49]. Each column is descretized
    by 4 degrees 0:4:356 as degrees
    
    (faxed doc also states that freq's could be reported to .was file,
    but I didn't find this so to be true)

    """

    import numpy
    from datetime import datetime
    from time import strptime

    # get sample datetime from filename
    fn = sensor_info['fn']
    sample_dt_start = filt_datetime(fn)

    # try getting sample date/times from .wap
    wap_fn = os.path.splitext(fn)[0] + ".wap"
    if os.path.exists(wap_fn):
        wap_lines = load_data(wap_fn)

        data = {
            'dt' : numpy.array(numpy.ones((len(wap_lines),), dtype=object)*numpy.nan),
            'time' : numpy.array(numpy.ones((len(wap_lines),), dtype=long)*numpy.nan),
            'press' : numpy.array(numpy.ones((len(wap_lines),), dtype=float)*numpy.nan),
            }
        i=0
        
        for line in wap_lines:
            # split line and parse float and integers
            wap = []
            sw = re.split(' ', line)
            for s in sw:
                m = re.search(REAL_RE_STR, s)
                if m:
                    wap.append(float(m.groups()[0]))
            
            # get sample datetime from data
            sample_str = '%02d-%02d-%4d %02d:%02d:%02d' % tuple(wap[0:6])
            if  sensor_info['utc_offset']:
                sample_dt = scanf_datetime(sample_str, fmt='%m-%d-%Y %H:%M:%S') + \
                            timedelta(hours=sensor_info['utc_offset'])
            else:
                sample_dt = scanf_datetime(sample_str, fmt='%m-%d-%Y %H:%M:%S')

            # these items can also be teased out of raw adcp but for now get from config file
            # th = sensor_info['transducer_ht']  # Transducer height above bottom (meters)
            
            # pressure (dbar) converted to water depth
            pressure = wap[17] # pressure (dbar) at tranducer height (?)
            # water_depth = th + sw_dpth(pressure, lat)

            data['dt'][i] = sample_dt
            data['time'][i] = dt2es(sample_dt)
            data['press'][i] = pressure # dbar
            i=i+1

    else:
        print "error: No corresponding .wap file"
        print " .... skipping %s" % (fn,)
        return data

    # assign specific fields
    nbursts = len(data['dt'])
    Df = 0.01 # (Hz)
    f = numpy.arange(0.02, 0.99, Df)
    nfreq = len(f)       # Number of frequencies (no units)

    # Did we get the number of data rows that we expected?  Should equal nfreq
    n = int(len(lines)/nfreq)
    if n != nbursts:
        print "Number of data rows %d does not match expected number %d" % (n, nbursts)
        print " .... skipping %s" % (fn,)
        return data
                            
    Dtheta = 1.0 # degrees 
    D = numpy.arange(0.0, 360.0, 4)
    D = numpy.mod(D,360)
    ndir = len(D)  # Number of directions (no units)

    # now get power spectra from .was 
    was_fn = os.path.splitext(fn)[0] + ".was"
    was_Sf = numpy.array(numpy.ones((nbursts,nfreq), dtype=float)*numpy.nan)
    if os.path.exists(was_fn):
        was_lines = load_data(was_fn)

        i=0
        # first line is freq label for each column start at [1]
        for line in was_lines[1:]: 
            # split line and parse float and integers
            was = []
            sw = re.split(' ', line)
            for s in sw:
                m = re.search(REAL_RE_STR, s)
                if m:
                    was.append(float(m.groups()[0]))
            
            # just the frequencies we have in directional spectra [0:nfreq]
            was_Sf[i] = was[0:nfreq] # (m^2/Hz) non-directional power spectrum for each sample time

            i=i+1

    else:
        print "error: No corresponding .was file"
        print " .... skipping %s" % (fn,)
        return data
        
    # add these keys, value pairs to dictionary "data" already setup after reading .wap
    data['dirs'] = numpy.array(numpy.ones((ndir,), dtype=float)*numpy.nan)
    data['freqs'] = numpy.array(numpy.ones((nfreq,), dtype=float)*numpy.nan)
    data['Sxx'] = numpy.array(numpy.ones((nbursts,nfreq,ndir), dtype=float)*numpy.nan)
    data['Sf'] = numpy.array(numpy.ones((nbursts,nfreq), dtype=float)*numpy.nan)
    data['Stheta'] = numpy.array(numpy.ones((nbursts,ndir), dtype=float)*numpy.nan)
    data['Stheta_swell'] = numpy.array(numpy.ones((nbursts,ndir), dtype=float)*numpy.nan)
    data['Stheta_wind'] = numpy.array(numpy.ones((nbursts,ndir), dtype=float)*numpy.nan)
    data['Hs'] = numpy.array(numpy.ones((nbursts,), dtype=float)*numpy.nan)
    data['Hs_swell'] = numpy.array(numpy.ones((nbursts,), dtype=float)*numpy.nan)
    data['Hs_wind'] = numpy.array(numpy.ones((nbursts,), dtype=float)*numpy.nan)
    data['Tm'] = numpy.array(numpy.ones((nbursts,), dtype=float)*numpy.nan)
    data['Tm_swell'] = numpy.array(numpy.ones((nbursts,), dtype=float)*numpy.nan)
    data['Tm_wind'] = numpy.array(numpy.ones((nbursts,), dtype=float)*numpy.nan)
    data['Tp'] = numpy.array(numpy.ones((nbursts,), dtype=float)*numpy.nan)
    data['Tp_swell'] = numpy.array(numpy.ones((nbursts,), dtype=float)*numpy.nan)
    data['Tp_wind'] = numpy.array(numpy.ones((nbursts,), dtype=float)*numpy.nan)
    data['Dm'] = numpy.array(numpy.ones((nbursts,), dtype=float)*numpy.nan)
    data['Dm_swell'] = numpy.array(numpy.ones((nbursts,), dtype=float)*numpy.nan)
    data['Dm_wind'] = numpy.array(numpy.ones((nbursts,), dtype=float)*numpy.nan)
    data['Dp'] = numpy.array(numpy.ones((nbursts,), dtype=float)*numpy.nan)
    data['Dp_swell'] = numpy.array(numpy.ones((nbursts,), dtype=float)*numpy.nan)
    data['Dp_wind'] = numpy.array(numpy.ones((nbursts,), dtype=float)*numpy.nan)

    # for each burst read nfreq lines
    for j in range(nbursts):
    
        i = 0
        Sxx = numpy.array(numpy.ones((nfreq,ndir), dtype=float)*numpy.nan)
        # each line is a freq, each column is a direction
        for line in lines[j*nfreq:nfreq*(j+1)]:
            wds = []
            # split line and parse float and integers
            sw = re.split(' ', line)
            for s in sw:
                m = re.search(REAL_RE_STR, s)
                if m:
                    wds.append(float(m.groups()[0]))
            
            # wds[] is in units of Normalized-Energy/degree from .wds
            # use power (m^2/Hz) at same time and freq from .was to get units of m^2/Hz/deg
            if len(wds) == ndir:
                Sxx[i,:] =  numpy.array(wds[:])*was_Sf[j,i]  # cross spectrum as m^2/Hz/deg
                i = i+1

        # Did we get the number of data rows that we expected?  Should equal nfreq
        if i != nfreq:
            print "Number of data rows %d does not match expected number %d" % (i, nfreq)


        # NOTE make fupper location dependent?? (add to config_files??)
        fupper = 0.65   # upper freq limit 0.65 Hz or wave periods less than T~1.538s
        iswell = f<=1/10.               # swell band for T>10s
        iwind = (f>1/10.) * (f<=fupper) # wind band 1/fupper<T<10s
        # NOTE about python boolean overloaded operator '*' == and == bitwise_and()
        iall = f<=fupper                # all wave freq upper limit

        # compute non-directional spectrum by integrating over all angles
        # Sxx(freq, dir)  sum axis=1 is along direction
        Sf = Sxx.sum(axis=1)*Dtheta
        # Sxx(freq, dir)  axis=0 is along freq 
        Stheta = Sxx[iall].sum(axis=0)*Df
        Stheta_s = Sxx[iswell].sum(axis=0)*Df
        Stheta_w = Sxx[iwind].sum(axis=0)*Df

        # compute zeroth-, first- and second-moment from the non-directional spectrum
        # all frequency ranges
        m0 = Sf[iall].sum()*Df
        m1 = (f[iall]*Sf[iall]).sum()*Df
        m2 = ((f[iall]**2)*Sf[iall]).sum()*Df
        # swell band
        m0s = Sf[iswell].sum()*Df
        m1s = (f[iswell]*Sf[iswell]).sum()*Df
        m2s = ((f[iswell]**2)*Sf[iswell]).sum()*Df
        # wind band
        m0w = Sf[iwind].sum()*Df
        m1w = (f[iwind]*Sf[iwind]).sum()*Df
        m2w = ((f[iwind]**2)*Sf[iwind]).sum()*Df
        
        # Significant Wave Height (Hs)
        Hs = 4*numpy.sqrt(m0)
        Hss = 4*numpy.sqrt(m0s)
        Hsw = 4*numpy.sqrt(m0w)

        # Mean Wave Period (Tm)
        Tm = m0/m1
        Tms = m0s/m1s
        Tmw = m0w/m1w
        
        # Peak Wave Period (Tp)
        # imax = Sf[iall]==Sf[iall].max()
        # Fp = f(imax)
        # Tp = 1/Fp[0]
        # This wave parameters added by SH (not in GV's matlab script)
        # one-liner version of above
        # Tp = 1/(f[Sf[iall]==Sf[iall].max()][0])
        # Tps = 1/(f[Sf[iswell]==Sf[iswell].max()][0])
        # Tpw = 1/(f[Sf[iwind]==Sf[iwind].max()][0])
        imax = Sf[iall]==Sf[iall].max()
        Tp = 1/(f[imax][0])
        imax = Sf[iswell]==Sf[iswell].max()
        Tps = 1/(f[imax][0])
    
        imax = Sf[iwind]==Sf[iwind].max()
        # account for offset of iwind by iswell in finding peak wind freq
        nswell = len(f[iswell])
        false_swell = numpy.array([False for i in range(nswell)])
        imax = numpy.concatenate((false_swell,imax))
        Tpw = 1/(f[imax][0])
        
        # mean direction of wave approach used by Kuik et al (1989)
        # Mean wave direction as a function of frequency
        # for all freq, wind and swell bands as adapted from GV's code
        # (polar_waves_cur_wds.m, version 8)
        pi = numpy.pi
        ac1 = numpy.cos(D*pi/180)
        as1 = numpy.sin(D*pi/180)
        
        ch0 = (ac1*Stheta*Dtheta).sum()
        sh0 = (as1*Stheta*Dtheta).sum()
        Dm = numpy.arctan2(sh0,ch0)*180/pi
        if Dm<0: Dm = Dm+360. 
        
        ch0s = (ac1*Stheta_s*Dtheta).sum()
        sh0s = (as1*Stheta_s*Dtheta).sum()
        Dms = numpy.arctan2(sh0s,ch0s)*180/pi
        if Dms<0: Dms = Dms+360.
        
        ch0w = (ac1*Stheta_w*Dtheta).sum()
        sh0w = (as1*Stheta_w*Dtheta).sum()
        Dmw = numpy.arctan2(sh0w,ch0w)*180/pi
        if Dmw<0: Dmw = Dmw+360.

        # Peak Wave Direction (Dp) defined as the direction which
        # corresponds to the "Peak frequency", or Fp.  Peak frequency is the
        # frequency at which the "Spectral density function" is at a
        # maximum.  The spectral density function gives the dependence
        # with frequency of the energy of the waves considered.  also
        # known as the one-dimensional spectrum or energy spectrum.
        # Definitions from Metocean Glossary
        # http://www.ifremer.fr/web-com/glossary
        #
        # This wave parameter added by SH (not in GV's matlab script)
        imax = Sf[iall]==Sf[iall].max()
        idir = numpy.squeeze(Sxx[imax,:]==Sxx[imax,:].max())
        if len(idir.shape)==2: idir = idir[0]
        if idir.any(): Dp = D[idir][0]
        else: Dp = numpy.nan
        
        imax = Sf[iswell]==Sf[iswell].max()
        idir = numpy.squeeze(Sxx[imax,:]==Sxx[imax,:].max())
        if len(idir.shape)==2: idir = idir[0]
        if idir.any(): Dps = D[idir][0]
        else: Dps = numpy.nan
        
        imax = Sf[iwind]==Sf[iwind].max()
        idir = numpy.squeeze(Sxx[imax,:]==Sxx[imax,:].max())
        if len(idir.shape)==2: idir = idir[0]
        if idir.any(): Dpw = D[idir][0]
        else: Dpw = numpy.nan
        
        # ---------------------------------------------------------------
        # data['dt'][j] =  sample_dt # already have
        data['dirs'] = D
        data['freqs'] = f
        
        data['Sxx'][j] = Sxx # full directional spectrum (m^2/Hz/deg)
        data['Sf'][j] = Sf   # non-directional spectrum (m^2/Hz)
        data['Stheta'][j] = Stheta # Energy from all freq from each direction
        data['Stheta_swell'][j] = Stheta_s
        data['Stheta_wind'][j] = Stheta_w
        
        data['Hs'][j] = Hs
        data['Hs_swell'][j] = Hss    
        data['Hs_wind'][j] = Hsw
        
        data['Tm'][j] = Tm
        data['Tm_swell'][j] = Tms    
        data['Tm_wind'][j] = Tmw
        
        data['Tp'][j] = Tp
        data['Tp_swell'][j] = Tps    
        data['Tp_wind'][j] = Tpw
        
        data['Dm'][j] = Dm
        data['Dm_swell'][j] = Dms    
        data['Dm_wind'][j] = Dmw
        
        data['Dp'][j] = Dp
        data['Dp_swell'][j] = Dps    
        data['Dp_wind'][j] = Dpw
        
        # if j==0:
        #     print " Hs(m)\t Tp(s)\t Tm(s)\t Dp(N)\t Dm(N)"
        # else: 
        #     print "%.2g\t %.2g\t %.2g\t %g\t %g" % (Hs, Tp, Tm, Dp, Dm)
        #     print "%.2g\t %.2g\t %.2g\t %g\t %g" % (Hss, Tps, Tms, Dps, Dms)
        #     print "%.2g\t %.2g\t %.2g\t %g\t %g" % (Hsw, Tpw, Tmw, Dpw, Dmw)
           
        # print "  Waves: All / Swell / Wind -- burst %d, start %d, end %d" % (j, j*nfreq, nfreq*(j+1))
        # print " Hs (m): %g /%g /%g" % (Hs, Hss, Hsw)
        # print " Tp (s): %g /%g /%g" % (Tp, Tps, Tpw)
        # print " Tm (s): %g /%g /%g" % (Tm, Tms, Tmw)
        # print " Dp (N): %g /%g /%g" % (Dp, Dps, Dpw)
        # print " Dm (N): %g /%g /%g" % (Dm, Dms, Dmw)

        del Sxx, Sf, Stheta, Stheta_w, Stheta_s
    # for each burst

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
        'f' : {'short_name': 'f',
               'long_name': 'Frequency',
               'standard_name': 'frequency',
               'units': 'Hz',
               },
        'd' : {'short_name': 'd',
               'long_name': 'Direction',
               'standard_name': 'direction',
               'reference':'clock-wise from True North',
               'units': 'deg',
               },
        # data variables
        'Sxx' : {'short_name': 'Sxx',
                'long_name': 'Directional Spectral Density Function',
                'definition': 'Distribution of the wave energy with both frequency and direction',
                'standard_name': 'wave_directional_spectral_density',
                'units': 'm2 Hz-1 deg-1',
                },
        'Sf' : {'short_name': 'Sf',
                'long_name': 'Spectral Density Function',
                'definition': 'Distribution of the wave energy with frequency from all directions',
                'standard_name': 'wave_spectral_density',
                'units': 'm2 Hz-1',
                },
        'Stheta' : {'short_name': 'St',
                    'long_name': 'Spectral Density Function',
                    'definition': 'Distribution of the wave energy with direction from all frequencies',
                    'standard_name': 'wave_directional_density',
                    'units': 'm2 deg-1',
                },
        'Stheta_swell' : {'short_name': 'Sts',
                          'long_name': 'Swell Spectral Density Function',
                          'definition': 'Distribution of the wave energy with direction from all swell frequencies',
                          'standard_name': 'swell_wave_directional_density',
                          'units': 'm2 deg-1',
                          },
        'Stheta_wind' : {'short_name': 'Stw',
                          'long_name': 'Wind Spectral Density Function',
                          'definition': 'Distribution of the wave energy with direction from all Wind frequencies',
                          'standard_name': 'wind_wave_directional_density',
                          'units': 'm2 deg-1',
                          },
        'Hs' : {'short_name': 'Hs',
                'long_name': 'Significant Wave Height',
                'definition': 'Four times the square root of the first moment of the wave spectrum (4*sqrt(m0))',
                'standard_name': 'significant_wave_height',
                'units': 'm',
                },
        'Hs_swell' : {'short_name': 'Hss',
                      'long_name': 'Significant Swell Wave Height',
                      'definition': 'Four times the square root of the first moment of the swell wave spectrum (4*sqrt(m0s))',
                      'standard_name': 'significant_swell_wave_height',
                      'units': 'm',
                      },
        'Hs_wind' : {'short_name': 'Hsw',
                      'long_name': 'Significant Wind Wave Height',
                      'definition': 'Four times the square root of the first moment of the wind wave spectrum (4*sqrt(m0w))',
                      'standard_name': 'significant_wind_wave_height',
                      'units': 'm',
                      },
        'Tp' : {'short_name': 'Tp',
                'long_name': 'Peak Wave Period',
                'definition': 'Period of strongest wave (Sf  maximum)',
                'standard_name': 'peak_wave_period',                          
                'units': 'sec',
                },
        'Tp_swell' : {'short_name': 'Tps',
                      'long_name': 'Peak Swell Wave Period',
                      'definition': 'Period of strongest swell (Sfs energy maximum)',
                      'standard_name': 'peak_swell_wave_period',                          
                      'units': 'sec',
                      },
        'Tp_wind' : {'short_name': 'Tpw',
                'long_name': 'Peak Wind Wave Period',
                'definition': 'Period of strongest wind wave (Sfw energy maximum)',
                'standard_name': 'peak_wind_wave_period',                          
                'units': 'sec',
                             },
        'Tm' : {'short_name': 'Tm',
                'long_name': 'Mean Wave Period',
                'definition': 'Zero-moment of the non-directional spectrum divided by the first-moment (m0/m1)',
                'standard_name': 'mean_wave_period',                          
                'units': 'sec',
                },
        'Tm_swell' : {'short_name': 'Tms',
                'long_name': 'Mean Swell Wave Period',
                'definition': 'Zero-moment of the non-directional spectrum divided by the first-moment (m0s/m1s)',
                'standard_name': 'mean_swell_wave_period',                          
                'units': 'sec',
                },
        'Tm_wind' : {'short_name': 'Tmw',
                'long_name': 'Mean Wind Wave Period',
                'definition': 'Zero-moment of the non-directional spectrum divided by the first-moment (m0w/m1w)',
                'standard_name': 'mean_wind_wave_period',                          
                'units': 'sec',
                },
        'Dp' : {'short_name': 'Dp',
                'long_name': 'Peak Wave Direction',
                'definition': 'Direction from which strongest waves (wave energy) are coming (dir of max(S(Tp,dir)',
                'standard_name': 'peak_wave_from_direction',                          
                'units': 'deg from N',
                'reference': 'clockwise from True North',
                           },
        'Dp_swell' : {'short_name': 'Dps',
                'long_name': 'Peak Swell Wave Direction',
                'definition': 'Direction from which strongest waves (swell energy) are coming (dir of max(S(Tps,dir)',
                'standard_name': 'peak_wave_from_direction',                          
                'units': 'deg from N',
                'reference': 'clockwise from True North',
                           },
        'Dp_wind' : {'short_name': 'Dpw',
                'long_name': 'Peak Wind Wave Direction',
                'definition': 'Direction from which strongest waves (wind wave energy) are coming (dir of max(S(Tpw,dir)',
                'standard_name': 'peak_wave_from_direction',                          
                'units': 'deg from N',
                'reference': 'clockwise from True North',
                           },
        'Dm' : {'short_name': 'Dm',
                'long_name': 'Mean Wave Direction',
                'definition': 'Mean direction from which strongest waves (wave energy max) are coming for all frequencies',
                'standard_name': 'mean_wave_from_direction',                          
                'units': 'deg from N',
                'reference': 'clockwise from True North',
                           },
        'Dm_swell' : {'short_name': 'Dms',
                'long_name': 'Mean Swell Wave Direction',
                'definition': 'Mean direction from which strongest waves (wave energy max) are coming for swell frequencies',
                'standard_name': 'mean_swell_wave_from_direction',                          
                'units': 'deg from N',
                'reference': 'clockwise from True North',
                           },
        'Dm_wind' : {'short_name': 'Dmw',
                'long_name': 'Mean Wind Wave Direction',
                'definition': 'Mean direction from which strongest waves (wave energy max) are coming for wind wave frequencies',
                'standard_name': 'mean_wind_wave_from_direction',                          
                'units': 'deg from N',
                'reference': 'clockwise from True North',
                           },
        }

    
    # dimension names use tuple so order of initialization is maintained
    dim_inits = (
        ('ntime', NC.UNLIMITED),
        ('nlat', 1),
        ('nlon', 1),
        ('nz', 1),
        ('nfreq', sensor_info['nfreq']),
        ('ndir', sensor_info['ndir']),
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
        ('f',  NC.FLOAT, ('nfreq',)),
        ('d',  NC.FLOAT, ('ndir',)),
        # data variables
        ('Sxx', NC.FLOAT, ('ntime','nfreq','ndir')),
        ('Sf', NC.FLOAT, ('ntime','nfreq')),
        ('Stheta', NC.FLOAT, ('ntime','ndir')),
        ('Stheta_swell', NC.FLOAT, ('ntime','ndir')),
        ('Stheta_wind', NC.FLOAT, ('ntime','ndir')),
        ('Hs', NC.FLOAT, ('ntime',)),
        ('Hs_swell', NC.FLOAT, ('ntime',)),
        ('Hs_wind', NC.FLOAT, ('ntime',)),
        ('Tp', NC.FLOAT, ('ntime',)),
        ('Tp_swell', NC.FLOAT, ('ntime',)),
        ('Tp_wind', NC.FLOAT, ('ntime',)),
        ('Tm', NC.FLOAT, ('ntime',)),
        ('Tm_swell', NC.FLOAT, ('ntime',)),
        ('Tm_wind', NC.FLOAT, ('ntime',)),
        ('Dp', NC.FLOAT, ('ntime',)),
        ('Dp_swell', NC.FLOAT, ('ntime',)),
        ('Dp_wind', NC.FLOAT, ('ntime',)),
        ('Dm', NC.FLOAT, ('ntime',)),
        ('Dm_swell', NC.FLOAT, ('ntime',)),
        ('Dm_wind', NC.FLOAT, ('ntime',)),
        )
    
    # subset data only to month being processed (see raw2proc.process())
    i = data['in']

    # var data 
    var_data = (
        ('lat',  platform_info['lat']),
        ('lon', platform_info['lon']),
        ('z', 0),
        ('f', data['freqs']),
        ('d', data['dirs']),
        #
        ('time', data['time'][i]),
        ('Sxx', data['Sxx'][i]),
        ('Sf', data['Sf'][i]),
        ('Stheta', data['Stheta'][i]),
        ('Stheta_swell', data['Stheta_swell'][i]),
        ('Stheta_wind', data['Stheta_wind'][i]),
        ('Hs', data['Hs'][i]),
        ('Hs_swell', data['Hs_swell'][i]),
        ('Hs_wind', data['Hs_wind'][i]),
        ('Tp', data['Tp'][i]),
        ('Tp_swell', data['Tp_swell'][i]),
        ('Tp_wind', data['Tp_wind'][i]),
        ('Tm', data['Tm'][i]),
        ('Tm_swell', data['Tm_swell'][i]),
        ('Tm_wind', data['Tm_wind'][i]),
        ('Dp', data['Dp'][i]),
        ('Dp_swell', data['Dp_swell'][i]),
        ('Dp_wind', data['Dp_wind'][i]),
        ('Dm', data['Dm'][i]),
        ('Dm_swell', data['Tm_swell'][i]),
        ('Dm_wind', data['Tm_wind'][i]),
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
        ('Sxx', data['Sxx'][i]),
        ('Sf', data['Sf'][i]),
        ('Stheta', data['Stheta'][i]),
        ('Stheta_swell', data['Stheta_swell'][i]),
        ('Stheta_wind', data['Stheta_wind'][i]),
        ('Hs', data['Hs'][i]),
        ('Hs_swell', data['Hs_swell'][i]),
        ('Hs_wind', data['Hs_wind'][i]),
        ('Tp', data['Tp'][i]),
        ('Tp_swell', data['Tp_swell'][i]),
        ('Tp_wind', data['Tp_wind'][i]),
        ('Tm', data['Tm'][i]),
        ('Tm_swell', data['Tm_swell'][i]),
        ('Tm_wind', data['Tm_wind'][i]),
        ('Dp', data['Dp'][i]),
        ('Dp_swell', data['Dp_swell'][i]),
        ('Dp_wind', data['Dp_wind'][i]),
        ('Dm', data['Dm'][i]),
        ('Dm_swell', data['Dm_swell'][i]),
        ('Dm_wind', data['Dm_wind'][i]),
       )

    return (global_atts, var_atts, var_data)

#
