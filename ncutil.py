#!/usr/bin/env python
# Last modified:  Time-stamp: <2011-05-05 15:31:37 haines>
"""
Create, update and load utilities for netcdf files
"""

from pycdf import *
import os
import numpy

def nc_create(ncFile, (global_atts, var_atts, dim_inits, var_inits, var_data)):
    """
    Create new netcdf file

    :Parameters:
        ncFile : string
           Path and name of file to create
        (global_atts, var_atts, dim_inits, var_inits, var_data) : tuple
           Global Attributes, Variable Attributes, Dimensions, Variable Dimensions, and Data 
           Everything you need to create a netCDF file.
    """
    try:
        # Open new netCDF file, overwrite if it exists, create if does not
        nc = CDF(ncFile, NC.WRITE|NC.CREATE|NC.TRUNC)
        # Automatically set define and data modes.
        nc.automode()
        #
        # GLOBALS
        for attrName in global_atts.keys():
            setattr(nc, attrName, global_atts[attrName])
        
        # DIMENSIONS
        for dim in dim_inits:
            dimName, dimValue = dim
            # print '%s = %d' % (dimName, dimValue)
            ncdim = nc.def_dim(dimName, dimValue)
        
        # VARIABLES
        for var in var_inits:
            varName, varType, varDim = var
            ncvar = nc.def_var(varName, varType, varDim)
            # add attributes
            for attrName in var_atts[varName].keys():
                setattr(ncvar, attrName, var_atts[varName][attrName])
            # setattr(ncvar, '_FillValue', numpy.nan)
            
        # add data
        nrecs = nc.inq_unlimlen()
        for var in var_data:
            varName, varData = var
            # print varName
            # print varData
            # print varData.shape
            ncvar = nc.var(varName)
            # e.g. lat = array(var_data['lat'])
            # if an array
            if type(varData) == numpy.ndarray:
                if ncvar.isrecord():
                    # time, ens, u, v
                    ncvar[nrecs:nrecs+len(varData)] = varData.tolist()
                else:
                    ncvar[:] = varData.tolist() # z
            else:
                # if tuple, sequence or scalar
                ncvar[:] = varData
        
        nc.close()
    except CDFError, msg:
        print "CDFError:", msg
        # if nc:
        #     nc.close()
        #     del(nc)

def nc_update(ncFile, (global_atts, var_atts, var_data)):
    """
    Create new netcdf file

    :Parameters:
        ncFile : string
          Path and name of file to create
        (global_atts, var_atts, var_data) : tuple
          Global Attributes, Variable Attributes and Data
          Everything you need to update a netCDF file.
    """
    try:
        # Open netCDF in write mode
        nc = CDF(ncFile, NC.WRITE)
        # Automatically set define and data modes.
        nc.automode()
        #
        # GLOBALS
        for attrName in global_atts.keys():
            setattr(nc, attrName, global_atts[attrName])
        
        # VARIABLES
        # update attributes
        for var in var_atts:
            varName, atts = var
            ncvar = nc.var(varName)
            for attrName in atts.keys():
                setattr(ncvar, attrName, atts[attrName])
            
        # update data
        nrecs = nc.inq_unlimlen()
        for var in var_data:
            varName, varData = var
            ncvar = nc.var(varName)
            # e.g. lat = array(var_data['lat'])
            # if an array
            if type(varData) == numpy.ndarray:
                if ncvar.isrecord():
                    # time, ens, u, v (with unlimited dimension)
                    ncvar[nrecs:nrecs+len(varData)] = varData.tolist()
                else:
                    ncvar[:] = varData.tolist() # z (limited dimension)
            else:
                # if tuple, sequence or scalar
                ncvar[:] = varData

        nc.close()
    except CDFError, msg:
        print "CDFError:", msg
        # if nc:
        #     nc.close()
        #     del(nc)

def nc_get_time(ncFile):
    """Get time array from file """
    try:
        nc = CDF(ncFile)
        ncvars = nc.variables()
        if 'time' in ncvars.keys():
            es = nc.var('time')[:]
            units = nc.var('time').units
        else:
            print "time variable not found in ", ncFile
        nc.close()
        return (es, units)
    except CDFError, msg:
        print "CDFError:", msg

                    
def nc_find_record_vars(ncFile):
    """Find which variable are record variables"""
    try:
        nc = CDF(ncFile)
        ncvars = nc.variables()
        # list which variables is a record variable
        var_list = [varName for varName in ncvars.keys() if nc.var(varName).isrecord()]
        nc.close()
        return var_list
    except CDFError, msg:
        print "CDFError:", msg
                    

def nc_replace_fillvalue(ncFile, newfillvalue=-99999.0):
    """
    Replaces any occurrence of old _FillValue with new one

    This function is useful for replacing the _FillValue global
    attribute and then searching the data for the old value and
    replacing it with the new one.

    :Parameters:
        ncFile : string
          Path and name of file to create

    :Other Parameters:
        newfillvalue : type match to data (generally float) 
          By default is -99999.0
    
    """
    try:
        nc = CDF(ncFile, NC.WRITE)
        nc.automode()
        oldfillvalue = nc._FillValue
        nc._FillValue = newfillvalue
        for v in nc.variables().keys():
            vd = nc.var(v)[:]
            if numpy.isnan(oldfillvalue):
                idx = numpy.isnan(vd)
            else:
                idx = vd == oldfillvalue
            if idx.any():
                vd[idx] =  nc._FillValue
                nc.var(v)[:] = vd        
        nc.close()
    except CDFError, msg:
        print "CDFError:", msg

def nc_rename_dimension(ncFile, oldname, newname):
    """ Rename dimension name """
    try:
        nc = CDF(ncFile, NC.WRITE)
        nc.definemode()
        for d in nc.dimensions().keys():
            if d==oldname: nc.dim(d).rename(newname)
        nc.close()
    except CDFError, msg:
        print "CDFError:", msg
                                

def nc_file_check(fns):
    """Check file or list of files to ensure it is a netcdf file
    If it is not, remove a file or files from the list"""
    if isinstance(fns, str):
        try:
            nc = CDF(fns)
            nc.close()
            new_fns = fns
        except CDFError, msg:
            print "CDFError:", msg, fns
            new_fns = None
        
    else:
        new_fns = []
        for fn in fns:
            try:
                nc = CDF(fn)
                nc.close()
                new_fns.append(fn)
            except CDFError, msg:
                print "CDFError:", msg, fn
        
    return tuple(new_fns)
    

def nc_load(ncFile, varsLoad='all', nameType='variable_name',
            ga_flag=True, va_flag=True):
    """
    Load netcdf file

    :Parameters:
        ncFile : string or list of strings
            Path and name of file to load
            If list, then CDFMF 

    :Other Parameters:
        nameType : string 'variable_name' (default) or 'standard_name'
            Defines naming convention to use for variable names as data
            are loaded.  Variable name is the name used to store data
            in file.  'standard_name' means use variable name based on
            variable attribute called 'standard_name' of netcdf variable.
        varLoad : string or tuple of strings
            specific variable names to be loaded into a sequence or scalar
            in python following specification set in nameType
            By default, all variables will be loaded.
        ga_flag : boolean flag
            By default, load the global file attributes
        va_flag : boolean flag
            By default, load the variable file attributes
            
    :Returns:
        (global_atts, var_atts, dim_inits, var_inits, var_data) : tuple
          Global Attributes, Variable Attributes, Dimensions, Variable Dimensions, and Variable Data
          Everything you need to create a netCDF file.

    """
    
    try:
        if isinstance(ncFile, str):
            # if only one file and it is a string
            nc = CDF(ncFile)
        else:
            # if multiple filenames 
            nc = CDFMF(tuple(set(ncFile)))

        ncdims = nc.dimensions(full=1)
        ncvars = nc.variables()

        # GLOBAL ATTRIBUTES (global_atts)
        if ga_flag:
            global_atts = nc.attributes()
        else:
            global_atts = {}

        # DIMENSIONS (dim_inits)
        dim_inits = [None for j in range(len(ncdims))]
        if len(ncdims)>0:
            for dimName,dimValue in ncdims.items():
                val,idx,isUN = dimValue
                if isUN:
                    dim_inits[idx] = (dimName, NC.UNLIMITED)
                else:
                    dim_inits[idx] = (dimName, val)

        if varsLoad == 'all':
            varNames = ncvars.keys()
        else:
            varNames = varsLoad

        # VARIABLE DIMENSIONS (var_inits)
        # gets init info for requested variables and original order

        # initialize with same number of original variables
        # so order can be preserved by idx
        var_inits = [None for j in range(len(ncvars))]
        if len(ncvars)>0:
            for varName in varNames:
                    val,shape,typ,idx = ncvars[varName]
                    var_inits[idx] = (varName, typ, val)

        # remove the None values from the list to preserve original order
        var_inits = [v for v in var_inits if v != None]
        
        # VARIABLE ATTRIBUTES (var_atts)
        # gets attributes of requested variables
        var_atts = {}
        if len(ncvars)>0 and va_flag:
            for var in varNames:
                varAttrs = nc.var(var).attributes()
                var_atts[var] = varAttrs

        # VARIABLE DATA (var_data)
        # loads requested variables, original order preserved as with var_inits
        var_data = [None for j in range(len(ncvars))]
        if len(ncvars)>0:
            for varName in varNames:
                val,shape,typ,idx = ncvars[varName]
                var_data[idx] = (varName, nc.var(varName)[:])

        var_data = [v for v in var_data if v != None]

        # type cast lists into tuples 
        dim_inits = tuple(dim_inits)
        var_inits = tuple(var_inits)
        var_data = tuple(var_data)

        nc.close()
        return (global_atts, var_atts, dim_inits, var_inits, var_data)
        
    except CDFError, msg:
        print "CDFError:", msg

        
