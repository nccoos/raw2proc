platform_info = {
    'id' : 'lsrb',
    'location' : 'Lookout Shoals, NC',
    'lat' : 34.3434,  # degrees true (-) south, (+) north
    'lon' : -76.42,   # degrees true (-) west, (+) east
    'mvar' : -9.967,  # degrees (-) west, (+) east
    'mean_water_depth' : -25.17, # meters (-) down, (+) up
    'mean_water_depth_time_period' : 'June 2005 - Sept 2005',
    'institution' : 'nccoos',
    # 
    'config_start_date' : '2005-06-23 00:00:00',
    'config_end_date' : '2005-09-22 00:00:00', # None or yyyy-mm-dd HH:MM:SS
    'packages' : ('adcp',),
    }
sensor_info = {
    'adcp' : { 'id' : 'adcp',
               'description' : 'Current profile data',
               'raw_dir' : '/seacoos/data/nccoos/level0/lsrb/adcp_bLogData/2005_06',
               'raw_file_glob' : 'lsrb_LogData_20050623*',
               'proc_dir' : '/seacoos/data/nccoos/level1/lsrb/adcp',
               'process_module' : 'proc_rdi_logdata_adcp',
               'utc_offset' : 4,      # hours offset to utc
               'nbins' : 69,
               'bin_size' : 0.5,      # meters
               'transducer_ht' : 0.5, # meters above the bottom
               'blanking_ht' : 1.6,   # meters above transducer
               },
    'adcpwaves' : {'id' : 'adcpwaves',
                   'description' : 'Directional wave data',
                   'raw_dir' : '/seacoos/data/nccoos/level0/lsrb/adcp_bLogData/2005_06',
                   'raw_file_glob' : 'lsrb_LogData_20050623*',
                   'proc_dir' : '/seacoos/data/nccoos/level1/lsrb/adcpwaves',
                   'process_module' : 'proc_rdi_logdata_dw',
                   'utc_offset' : 4,  # hours offset to utc
                   'ndir' : 90.,
                   'nfreq' : 128.,
                   },
    }
    
