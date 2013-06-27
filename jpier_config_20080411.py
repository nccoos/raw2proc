platform_info = {
 	    'id' : 'jpier',
 	    'location' : 'Jennettes Pier, Nags Head, NC',
 	    'lat' : 35.9101,         # degrees true (-) south, (+) north
 	    'lon' : -75.5958,         # degrees true (-) west, (+) east
 	    'mvar' : -10.83333,      # degrees (-) west, (+) east        
            'mean_water_depth' : -11.38, # meters (-) down, (+) up
            'mean_water_depth_time_period' : 'May 2008 - Oct 2008',
 	    'institution' : 'nccoos',
 	    #
 	    'config_start_date' : '2008-04-11 00:00:00',
 	    'config_end_date' : '2008-07-21 23:00:00', # None or yyyy-mm-dd HH:MM:SS
 	    'packages' : ('adcp', 'adcpwaves'),
 	    }
sensor_info = {
    'adcp' : { 'id' : 'adcp',
               'description' : 'Current profile data',
               'raw_dir' : '/seacoos/data/nccoos/level0/jpier/adcp_ascii',
               'raw_file_glob' : '*.wpa',
               'proc_dir' : '/seacoos/data/nccoos/level1/jpier/adcp',
               'process_module' : 'proc_nortek_wpa_adcp',
               'utc_offset' : 4,      # hours offset to utc
               'nbins' : 34,
               'bin_size' : 0.5,      # meters
               'transducer_ht' : 0.5, # meters above the bottom
               # 'blanking_ht' : 0.41,  # meters above transducer
               'blanking_ht' : 1.9,  # meters above transducer
               'latest_dir' : '/seacoos/data/nccoos/latest_v2.0',
               'latest_vars' : ('time','lat','lon','z','u','v'),
               },
    'adcpwaves' : {'id' : 'adcpwaves',
                   'description' : 'Directional wave data',
                   'raw_dir' : '/seacoos/data/nccoos/level0/jpier/adcp_ascii',
                   'raw_file_glob' : '*.wds',
                   'proc_dir' : '/seacoos/data/nccoos/level1/jpier/adcpwaves',
                   'process_module' : 'proc_nortek_wds_dw',
                   'utc_offset' : 4,  # hours offset to utc
                   'ndir' : 90.,
                   'nfreq' : 97.,
                   'latest_dir' : '/seacoos/data/nccoos/latest_v2.0',
                   'latest_vars' : ('time','lat','lon','z','Tp','Hs'),
                   },

        }
