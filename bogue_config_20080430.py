platform_info = {
    'id' : 'bogue',
    'location' : 'Bogue Inlet Pier, Bogue, NC',
    'lat' : 34.661568,  # degrees true (-) south, (+) north
    'lon' : -77.034131, # degrees true (-) west, (+) east
    'mvar' : -9.7,      # degrees (-) west, (+) east
    'mean_water_depth' : -8.14, # meters (-) down, (+) up
    'mean_water_depth_time_period' : 'June 2006 - June 2008',
    'institution' : 'nccoos',
    # 
    'config_start_date' : '2008-04-30 16:00:00',
    'config_end_date' : '2008-07-02 00:00:00', # None or yyyy-mm-dd HH:MM:SS
    'packages' : ('adcp', 'adcpwaves'),
    }
sensor_info = {
    'adcp' : { 'id' : 'adcp',
               'description' : 'Current profile data',
               'raw_dir' : '/seacoos/data/nccoos/level0/bogue/adcp_bLogData',
               'raw_file_glob' : '*',
               'proc_dir' : '/seacoos/data/nccoos/level1/bogue/adcp',
               'process_module' : 'proc_rdi_logdata_adcp',
               'utc_offset' : 4,      # hours offset to utc
               'nbins' : 50,
               'bin_size' : 0.5,      # meters
               'transducer_ht' : 0.5, # meters above the bottom
               'blanking_ht' : 1.6,   # meters above transducer
               'latest_dir' : '/seacoos/data/nccoos/latest_v2.0',
               'latest_vars' : ('time','lat','lon','z','u','v'),
               },
    'adcpwaves' : {'id' : 'adcpwaves',
                   'description' : 'Directional wave data',
                   'raw_dir' : '/seacoos/data/nccoos/level0/bogue/adcp_cSpecData',
                   'raw_file_glob' : 'DSpec*',
                   'proc_dir' : '/seacoos/data/nccoos/level1/bogue/adcpwaves',
                   'process_module' : 'proc_rdi_dspec_dw',
                   'utc_offset' : 4,  # hours offset to utc
                   'ndir' : 90.,
                   'nfreq' : 128.,
                   'latest_dir' : '/seacoos/data/nccoos/latest_v2.0',
                   'latest_vars' : ('time','lat','lon','z','Tp','Hs'),
                   },
    }
    
