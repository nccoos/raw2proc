platform_info = {
    'id' : 'ouba',
    'location' : 'Outer Banks, NC',
    ##### use bounding box (limits or polygon) to describe location
    'lat' :  (34.5, 38.),  # degrees true (-) south, (+) north
    'lon' :  (-76, -73.), # degrees true (-) west, (+) east
    'mvar' : -11,      # degrees (-) west, (+) east
    'nlat' : 65.,
    'nlon' : 45.,
    # 'mean_water_depth' : -8.14, # meters (-) down, (+) up
    # 'mean_water_depth_time_period' : 'June 2006 - June 2008',
    'institution' : 'nccoos',
    # 
    'config_start_date' : '2010-07-01 00:00:00',
    'config_end_date' : None, # None or yyyy-mm-dd HH:MM:SS
    'packages' : ('hfr', ),
    }
sensor_info = {
    'hfr' : { 'id' : 'hfr',
              'description' : 'High Frequency RADAR Surface Current Totals',
              'raw_dir' : '/seacoos/data/nccoos/level0/ouba/hfr_totals',
              'raw_file_glob' : '*.tuv',
              'proc_dir' : '/seacoos/data/nccoos/level1/ouba/hfr_totals',
              'process_module' : 'proc_codar_totals',
              'utc_offset' : 0,      # hours offset to utc
              'operating_frequency' : 4.5,    # MHz
              'averaging_radius' : 9.0,      # kilometers
               # 'plot_module' : 'ouba_totals_plot', 
               # 'plot_names' : ('vecmap',), 
               # 'csv_dir' : '/seacoos/data/nccoos/latest_csv',
               # 'cvs_vars' : ('time','lat','lon','z','u','v'),
               'latest_dir' : '/seacoos/data/nccoos/latest_v2.0',
               'latest_vars' : ('time','lat','lon','z','u','v'),
               },
    }
    
## NOTE: grid definition for totals based on 6km spacing and the bounding box
# minlat, maxlat =  (34.5, 38.)
# minlon, maxlon =  (-76, -73.)
# midlat = minlat + 0.5*(maxlat-minlat)
## ~111 km = 1 deg latitude
# nlat = numpy.round((maxlat-minlat) *111/6)
# nlon = numpy.round((maxlon-minlon) * math.cos(midlat*math.pi/180)*111/6)

