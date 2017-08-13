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
        self._credentials = {'MFP_USER':None,'STRAVA_TOKEN':None}
        self.mfp_client = None
        self.stv_client = None
        
        #Do we need to update the database?
        today = datetime.datetime.today()
        last_update,final = self.get_last_entry()
        #Initialize the db
        if last_update == None:
            self._read_creds()
            self.mfp_client = self._make_client('mfp')
            self.stv_client = self._make_client('strava')
            if not None in (self.mfp_client,self.stv_client):
                self._init_db()
        
        elif last_update.date() < today.date():
            self._read_creds()
            self.mfp_client = self._make_client('mfp')
            self.stv_client = self._make_client('strava')
            over_write = False
            if final == 0:
                over_write = True
            self.update_db(last_update,over_write = over_write)
        
            
    
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
                        if self._credentials.has_key(key):
                            self._credentials[key] = attribute
    def _make_client(self,mode):
        """Make a client of type 'mode'"""
        if mode == 'mfp':
            try:
                client = mfp.Client(self._credentials['MFP_USER'])
                return client
            except:
                print "Invalid credentials supplied for myfitnesspal."
                return None
        if mode == 'strava':
            try:
                client = strava.Client(access_token = self._credentials['STRAVA_TOKEN'])
                return client
            except:
                print "Invalid credentials supplied for strava."
                return None
            
    def _init_db(self):
        """Initialize the db if no files are found"""
        print "Initializing the database..."
        #Calorie file
        #If we found the file don't remake it
        today  = datetime.date.today()
        if os.path.isfile(DB_CAL):
            print "\tFound calorie info. Skipping."
        else:
            print "\tUpdating db calorie file"
            datestr = raw_input("\tDate you began logging calories (%s): "%self.date_fmt)
            date = self._set_date_(datestr)
            date = date.date()
            if date:
                with open(DB_CAL, 'w') as calfile:
                    while date <= datetime.date.today():
                        print date
                        mfpdate = self.mfp_client.get_date(date)
                        if mfpdate.totals:
                            cals = mfpdate.totals['calories']
                            goal = mfpdate.goals['calories']
                        else:
                            cals = -1
                            goal = -1
                        final = 0
                        if date < today:
                            final = 1
                        line = "%s,%s,%s,%s\n"%(date,cals,goal,final)
                        calfile.write(line)
                        date = date + datetime.timedelta(days = 1)
        #Weight file
        if os.path.isfile(DB_WGT):
            print "\tFound weight info. Skipping."
        else:
            print "\tUpdating db weight file."
            try: 
                d = datestr
            except NameError:
                datestr = raw_input("\tDate you began tracking weight (%s): "%self.date_fmt)
            date = self._set_date_(datestr)
            wts = self.mfp_client.get_measurements(lower_bound = date.date())
            with open(DB_WGT, 'w') as wtfile:
                for key in sorted(wts.keys()):
                    wt = wts[key]
                    line = "%s,%s\n"%(key,wt)
                    wtfile.write(line)
            
        #Workout file
        if os.path.isfile(DB_RUN):
            print "\tFound run info. Skipping."
        else:
            print "\tUpdating db running file."
            athlete = self.stv_client.get_athlete()
            date = athlete.created_at
            acts = self.stv_client.get_activities(after = date)
            with open(DB_RUN,'w') as runfile:
                for act in acts:
                    if act.type == 'Run':
                        date = act.start_date_local
                        dist = act.distance
                        time = act.elapsed_time
                        line = "%s,%s,%s\n"%(date,dist,time)
                        runfile.write(line)
                        
    def remove_last_line(fname):
        """Remove the last line of a file"""
        if os.path.isfile(fname):
            lines = []
            with open(fname) as f:
                lines = f.readlines()
            with open(fname,'w') as f:
                wlines = lines[:-1]
                f.writelines(wlines)
            return True
        else:
            return False
                        
    def update_db(self,date,over_write = False):
        """Get new data from and add to db"""
        date = self._set_date_(date)
        if date:
            date = date + datetime.timedelta(days = 1) #Dont repeat the last line
            
        if os.path.isfile(DB_CAL) and date: 
            cdate = date.date()
            if over_write:
                date = date - datetime.timedelta(days = 1)
                if remove_last_line(DB_CAL):
                    self.update_db(date)
            else:
                with open(DB_CAL,'a') as calfile:
                    iter_date = cdate
                    while iter_date <= datetime.date.today():
                        mfpdate = self.mfp_client.get_date(iter_date)
                        if mfpdate.totals:
                            cals = mfpdate.totals['calories']
                            goal = mfpdate.goals['calories']
                        else:
                            cals = -1
                            goal = -1
                        final = 0
                        if iter_date < datetime.date.today():
                            final = 1
                        line = "%s,%s,%s,%s\n"%(iter_date,cals,goal,final)
                        calfile.write(line)
                        iter_date = iter_date + datetime.timedelta(days = 1)
        
        if os.path.isfile(DB_WGT) and date:
            if type(date) == datetime.datetime:
                wdate = date.date()
            wts = self.mfp_client.get_measurements(lower_bound = wdate)
            with open(DB_WGT, 'a') as wtfile:
                for key in sorted(wts.keys()):
                    wt = wts[key]
                    line = "%s,%s\n"%(key,wt)
                    wtfile.write(line)
                    
        if os.path.isfile(DB_RUN) and date:
            if type(date) == datetime.date:
                time = datetime.time(0,0,0)
                date = datetime.datetime.combine(date,time)
            acts = self.stv_client.get_activities(after = date)
            with open(DB_RUN,'a') as runfile:
                for act in acts:
                    if act.type == 'Run':
                        date = act.start_date_local
                        dist = act.distance
                        time = act.elapsed_time
                        line = "%s,%s,%s\n"%(date,dist,time)
                        runfile.write(line)
            
                        
    def get_last_entry(self):
        """Retrieve the date of the most recent entry"""
        if not os.path.isfile(DB_CAL):
            return None,None
        else:
            lastline = ""
            with open(DB_CAL) as calfile:
                for line in calfile:
                    lastline = line
            split = lastline.split(',')
            datestr = split[0]
            final = (split[-1]).strip()
            date = self._set_date_(datestr)
            return date,final
        
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
        
                
        