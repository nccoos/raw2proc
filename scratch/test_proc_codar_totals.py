#!/usr/bin/env python
# Last modified:  Time-stamp: <2013-04-26 13:47:44 haines>
"""
parse datestr from cr1000 files to create monthly files

input file
/seacoos/data/nccoos/level0/crow/crow_csi_loggernet_yyyymmdd-yyyymmdd.dat

Output form
/seacoos/data/nccoos/level0/crow/yyyy_mm/wq/csi_wq_yyyy_mm.dat
/seacoos/data/nccoos/level0/crow/yyyy_mm/flow/csi_flow_yyyy_mm.dat

load data file
parse lines for time YYYY, jjj, HHMM
what year and month?

create YYYY_MM directory and output file if does not exist.
write line to YYYY_MM/csi_loggernet_yyyy_mm.dat output file

"""

REAL_RE_STR = '\\s*(-?\\d(\\.\\d+|)[Ee][+\\-]\\d\\d?|-?(\\d+\\.\\d*|\\d*\\.\\d+)|-?\\d+)\\s*'

import sys
import os
import re
from procutil import *

def parser_codar(fn, lines):
    """
    parse and assign data to variables from CODAR Totals LLUV format

    Notes
    -----
    1. Requires grid definition  
    
    """

    import numpy
    from datetime import datetime
    from time import strptime
    from StringIO import StringIO
    from matplotlib.mlab import griddata

    # get sample datetime from filename
    # fn = sensor_info['fn']
    sample_dt_start = filt_datetime(fn)

    # read header that match '%(k): (v)\n' pairs on each line
    m = re.findall(r'^(%.*):\s*(.*)$', ''.join(lines), re.MULTILINE)
    for k,v in m:        
        if k == '%TimeStamp':
            sample_dt = scanf_datetime(v, fmt='%Y %m %d %H %M %S')
            
        elif k == '%TableType':
            ftype = v
        elif k == '%TableColumns':
            ncol = int(v)
        elif k == '%TableRows':
            nrow = int(v)

    # read data from string of lines but make it behave like a file object with StringIO
    s = StringIO(''.join(lines))
    s.seek(0) # ensures start posn of file
    d = numpy.loadtxt(s, comments='%')
    # lat, lon, u, v = numpy.loadtxt(s, usecols=(0,1,2,3), comments='%', unpack=True)
    if 'TOT4' in ftype:
        lon = d[:,0]
        lat = d[:,1]
        wu = d[:,2]
        wv = d[:,3]
        gridflag = d[:,4]
        wu_std_qual = d[:,5]
        wv_std_qual = d[:,6]
        cov_qual = d[:,7]
        x_dist = d[:,8]
        y_dist = d[:,9]
        rang = d[:,10]
        bearing = d[:,11]
        vel_mag = d[:,12]
        vel_dir = d[:,13]
        # s1 = d[:,14]
        # s2 = d[:,15]
        # s3 = d[:,16]
        # s4 = d[:,17]
        # s5 = d[:,18]
        # s6 = d[:,19]

    # define the lat/lon grid based on 6km resolution
    # For Outer Banks north and east of Cape Hatteras, bounding box is defined by:
    minlat, maxlat = (34.5, 38)
    minlon, maxlon = (-76, -73.)
    midlat = minlat + 0.5*(maxlat-minlat)
    # ~111 km = 1 deg latitude
    nlat = numpy.round((maxlat-minlat) *111/6)
    nlon = numpy.round((maxlon-minlon) * math.cos(midlat*math.pi/180)*111/6)
    yi = numpy.linspace(minlat, maxlat, nlat)
    xi = numpy.linspace(minlon, maxlon, nlon)
    uim = griddata(lon, lat, wu, xi, yi)
    vim = griddata(lon, lat, wv, xi, yi)
    # returned masked array as an ndarray with masked values filled with fill_value
    ui = uim.filled(fill_value=numpy.nan)
    vi = vim.filled(fill_value=numpy.nan)
    # ---------------------------------------------------------------
    data = {
        'dt' : numpy.array(numpy.ones((1,), dtype=object)*numpy.nan),
        'time' : numpy.array(numpy.ones((1,), dtype=long)*numpy.nan),
        'lon' : numpy.array(numpy.ones((1,nlon), dtype=float)*numpy.nan),
        'lat' : numpy.array(numpy.ones((1,nlat), dtype=float)*numpy.nan),
        'u' : numpy.array(numpy.ones((1,nlon,nlat), dtype=float)*numpy.nan),
        'v' : numpy.array(numpy.ones((1,nlon,nlat), dtype=float)*numpy.nan),
        }
    # ---------------------------------------------------------------
    i = 0
    data['dt'][i] =  sample_dt # 
    data['time'][i] =  dt2es(sample_dt) # 
    data['lon'][i] = xi # new longitude grid
    data['lat'][i] = yi # new latitude grid
    data['u'][i] = ui.T # u-component of water velocity (cm/s)
    data['v'][i] = vi.T # v-component of water velocity 

    return data


def load_data(inFile):
    lines=None
    if os.path.exists(inFile):
        f = open(inFile, 'r')
        lines = f.readlines()
        f.close()
        if len(lines)<=0:
            print 'Empty file: '+ inFile           
    else:
        print 'File does not exist: '+ inFile
    return lines

from raw2proc import *

def test1(fn):
    lines = load_data(fn)
    return parser_codar(fn, lines)


if __name__ == '__main__':
    # LLUV Spec < 1.17
    # fn = '/seacoos/data/nc-coos/level0/ouba/hfr_totals/2010_07/TOTL_OUBA_2010_07_14_0000.tuv'
    fn = '/seacoos/data/nc-coos/level0/ouba/hfr_totals/2013_04/TOTL_OUBA_2013_04_26_1100.tuv'

    # 
    # fn = sys.argv[1]
    try:
        test1(fn)
    except:
        pass
    
