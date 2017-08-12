#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sat Aug 12 09:11:57 2017

@author: tjwilliamson

A class to interface with myfitnesspal and strava
to track my fitness data
"""

import myfitnesspal as mfp
import stravalib as strava
import datetime
import numpy as np

class FitnessData(object):
    
    def __init__(self,start_date = None, stop_date = None):
    
    
    def _set_date_(self,date):
        """Make sure date is a valid object"""
        if type(date) in (datetime.date,datetime.datetime):
            return date
        
        elif type(date) == str:
    
    def _read_date_string(datestr):
        """Guess date format and read string into datetime"""
        

