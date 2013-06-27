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
    'config_start_date' : '2009-09-15 00:00:00',
    'config_end_date' : '2010-01-11 00:00:00', # None or yyyy-mm-dd HH:MM:SS
    'packages' : ('adcp', 'adcpwaves'),
    }
sensor_info = {
    'adcp' : { 'id' : 'adcp',
               'description' : 'Current profile data',
               'raw_dir' : '/seacoos/data/nccoos/level0/bogue/adcp_ascii',
               'raw_file_glob' : '*.wpa',
               'proc_dir' : '/seacoos/data/nccoos/level1/bogue/adcp',
               'process_module' : 'proc_nortek_wpa_adcp',
               'utc_offset' : 0,      # hours offset to utc
               'nbins' : 20,
               'bin_size' : 0.5,      # meters
               'transducer_ht' : 0.75, # meters above the bottom
               'blanking_ht' : 0.9,  # meters above transducer
               'plot_module' : 'bogue_adcp_plot', 
               'plot_names' : ('timeseries',), 
               # 'csv_dir' : '/seacoos/data/nccoos/latest_csv',
               # 'cvs_vars' : ('time','lat','lon','z','u','v','wd','wl'),
               # 'latest_dir' : '/seacoos/data/nccoos/latest_v2.0',
               # 'latest_vars' : ('time','lat','lon','z','u','v','wd','wl'),
               },
    'adcpwaves' : {'id' : 'adcpwaves',
                   'description' : 'Directional wave data',
                   'raw_dir' : '/seacoos/data/nccoos/level0/bogue/adcp_ascii',
                   'raw_file_glob' : '*.wds',
                   'proc_dir' : '/seacoos/data/nccoos/level1/bogue/adcpwaves',
                   'process_module' : 'proc_nortek_wds_dw',
                   'utc_offset' : 0.,  # hours offset to utc
                   'ndir' : 90.,
                   'nfreq' : 97.,
                   'plot_module' : 'bogue_waves_plot', 
                   'plot_names' : ('allwaves', 'swellwaves', 'windwaves'), 
                   # 'csv_dir' : '/seacoos/data/nccoos/latest_csv',
                   # 'csv_vars' : ('time','lat','lon','z','Tp','Hs'),
                   # 'latest_dir' : '/seacoos/data/nccoos/latest_v2.0',
                   # 'latest_vars' : ('time','lat','lon','z','Tp','Hs'),
                   },
    }
    
