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
 	    'config_start_date' : '2005-04-25 00:00:00',
 	    'config_end_date' : '2008-04-11 00:00:00', # None or yyyy-mm-dd HH:MM:SS
 	    'packages' : ('met',),
 	    }
sensor_info = {
 	    'met' : { 'id' : 'met',
			'description' : 'Met data',
			'raw_dir' : '/seacoos/data/nccoos/level0/jpier/met/',
                        'utc_offset' : 4,      # hours offset to utc
			'raw_file_glob' : '*.jpierMet.stats',
			'proc_dir' : '/seacoos/data/nccoos/level1/jpier/met/',
			'process_module' : 'proc_jpier_ascii_met',
			},
		}
