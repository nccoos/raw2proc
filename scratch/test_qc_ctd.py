
import pydap.client
import pprint

# dataset = open_url('http://test.opendap.org/dap/data/nc/coads_climatology.nc')
data = pydap.client.open_url('http://whewell.marine.unc.edu/dods/nccoos/level1/b1/ctd2/b1_ctd2_2012_04.nc')
pprint.pprint(d1.attributes)

wtemp=data['wtemp'].array[:]
# QC before
good = (5<wtemp) & (wtemp<30)
bad = ~good
wtemp[bad] = numpy.nan 

cond = data['cond'].array[:]
good = (2<cond) & (cond<6)
bad = ~good
cond[bad] = numpy.nan 

