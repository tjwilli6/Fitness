#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 15 18:58:54 2017

@author: tjwilliamson
"""

import numpy as np
from astropy.time import Time
import datetime
import warnings

def binned(x, y, numbins = 10, binsize = None, average = False):
    """Bin ydata by xdata in bins. Return bin_edges, bin_widths, bin_ctrs, ydata"""
    dat_type = type(x[0])
    #Is our x axis a datetime object? If so convert to MJD
    do_dates = False
    if dat_type in (datetime.date,datetime.datetime):
        x = datetime_to_mjd(x)
        do_dates = True
    
    xdata = np.array(x)
    ydata = np.array(y)
    
    #Define the bins on x axis
    if binsize:
        if isinstance(binsize,int) or isinstance(binsize,float):
            bins = _get_bins_from_size(xdata,binsize)
        else:
            if isinstance(numbins,int) or isinstance(numbins,float):
                bins = int(numbins)
                bins = _get_bins_from_binnum(xdata,numbins)
            else:
                #Invalid binsize and invalid binnums
                warnings.warn("No valid 'bins' or 'binsize' argument. Returning original data.")
                return x,y
    elif numbins:
        if isinstance(numbins,int) or isinstance(numbins,float):
            bins = int(numbins)
            bins = _get_bins_from_binnum(xdata,numbins)
        else:
            warnings.warn("No valid 'bins' or 'binsize' argument. Returning original data.")
            return x,y
    
    #Bin the data
    inds = np.digitize(xdata,bins)
    ybins = np.zeros_like(bins)
    binhits = np.zeros_like(ybins)
    for i,y in enumerate(ydata):
        ind = inds[i] - 1
        ybins[ind] += y
        binhits[ind] += 1
        
    if average:
        binhits[binhits == 0] = 1
        ybins = ybins / binhits
    #We need to get get the size of each bin
    #binwidths = bins[1:] - bins[:-1]
    bincenters = bins + float(binsize) / 2
    
    if do_dates:
        bins = mjd_to_datetime(bins)
        bincenters = mjd_to_datetime(bincenters)
        
    return bins,bincenters,ybins
    
            

def _get_bins_from_size(x, binsize):
    """Get bins from x data and a given size"""
    eps = np.finfo(float).eps
    xdata = np.array(x)
    bins = np.arange(xdata.min(),xdata.max() + eps,binsize)
    if bins[-1] < xdata.max():
        bins = np.append(bins,xdata.max())
    return bins

def _get_bins_from_binnum(x,binnum):
    """Get bins from x data and a specified number of bins"""
    xdata = np.array(x)
    freq,bins = np.histogram(xdata, bins = binnum)
    return bins

def datetime_to_mjd(x):
    """Convert an array of datetime objects to MJD"""
    try:
        time_data = np.array([Time("%s"%t).mjd for t in x])
        return time_data
    except:
        return x
    
def mjd_to_datetime(x,onlydate = False):
    """Convert an array of MJD objects to datetime"""
    try:
        time_data = np.array([Time(t, format = 'mjd').datetime for t in x])
        if onlydate:
            time_data = np.array([t.date() for t in time_data])
        return time_data
    except:
        return x
