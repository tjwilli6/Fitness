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
import os
import numpy as np

#Define file names
CREDENTIALS = 'credentials.txt'
DB_WGT = 'db/mfpwt.dat'
DB_CAL = 'db/mfpcl.dat'
DB_RUN = 'db/st_rn.dat'

class FitnessData(object):
    
    def __init__(self,start_date = None, stop_date = None, date_fmt = '%Y-%m-%d'):
        #Read inputs and define variables
        self.date_fmt = date_fmt
        self._start_date = self._set_date_(start_date)
        self._stop_date = self._set_date_(stop_date)
        self._credentials = {"MFP_USER":None,"STRAVA_TOKEN":None}
        
        #Do we need to update the database?
        today = datetime.datetime.today()
        last_update = self.get_last_entry()
    
    def _set_date_(self,date):
        """Make sure date is a valid object"""
        #If it is already a datetime object, or None
        if type(date) in (datetime.date,datetime.datetime,type(None)):
            return date
        #If it's a string, turn it into a datetime
        elif type(date) == str:
            try:
                date_obj = datetime.datetime.strptime(date,self.date_fmt)
            except ValueError as e:
                print e.args[0]
                date_obj = None
            return date_obj
        else:
            print "Cannot make type %s into date object."%type(date)
            return None
    
    def _read_creds(self):
        """Read login credentials"""
        if not os.path.isfile(CREDENTIALS):
            return {'MFPUSER':None,'STRAVATOKEN':None}
        else:
            with open(CREDENTIALS) as f:
                for line in f:
                    split = [l.strip() for l in line.split(':')]
                    if len(split) == 2:
                        key,attribute = split
                        if self.credentials.has_key(key):
                            self.credentials[key] = attribute
    def get_last_entry(self):
        """Retrieve the date of the most recent entry"""
        if not os.path.isfile(DB_CAL):
            return None
        else:
            lastline = ""
            with open(DB_CAL) as calfile:
                for line in calfile:
                    lastline = line
            datestr = lastline.split(',')[0]
            date = self._set_date_(datestr)
            return date
        
    @property
    def start_date(self):
        return self._start_date
    
    @property
    def stop_date(self):
        return self._stop_date
    
    @start_date.setter
    def start_date(self,date):
        self._start_date = self._set_date_(date)
    
    @stop_date.setter
    def stop_date(self,date):
        self._stop_date = self._set_date_(date)
        
                
        