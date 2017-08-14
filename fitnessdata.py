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
import matplotlib.pyplot as plt

#Define file names
CREDENTIALS = 'credentials.txt'
DB_WGT = 'db/mfpwt.dat'
DB_CAL = 'db/mfpcl.dat'
DB_RUN = 'db/st_rn.dat'

class FitnessData(object):
    """This is a docstring"""
    def __init__(self,start_date = None, stop_date = None, date_fmt = '%Y-%m-%d',height = 66.):
        #Read inputs and define variables
        self.date_fmt = date_fmt
        self._start_date = self._set_date_(start_date)
        self._stop_date = self._set_date_(stop_date)
        self._credentials = {'MFP_USER':None,'STRAVA_TOKEN':None}
        self.mfp_client = None
        self.stv_client = None
        self.height = height
        
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
        #Update the db
        elif last_update < today.date():
            self._read_creds()
            self.mfp_client = self._make_client('mfp')
            self.stv_client = self._make_client('strava')
            over_write = False
            if final == '0':
                over_write = True
            self.update_db(last_update,over_write = over_write)
        
        #Read data files into arrays
        self._caldate = []
        self._calcons = []
        self._calgoal = []
        
        self._wtdate = []
        self._wt = []
        
        self._rundate = []
        self._rundist = []
        self._runtime = []
        
        cal_list = self.readfile(DB_CAL)
        wt_list = self.readfile(DB_WGT)
        run_list = self.readfile(DB_RUN)
        
        if len(cal_list) == 4:
            self._caldate,self._calcons,self._calgoal,final = cal_list
            #Mask these guys
            self._calcons = np.ma.masked_where(self._calcons < 0,self._calcons)
            self._calgoal = np.ma.masked_where(self._calgoal < 0,self._calgoal)
        if len(wt_list) == 2:
            self._wtdate,self._wt = wt_list
        if len(run_list) == 3:
            self._rundate,self._rundist,self._runtime = run_list
        
        
        
        
        
        
        
    
    def _set_date_(self,date):
        """Make sure date is a valid object"""
        #If it is already a datetime object, or None
        if type(date) in (datetime.date,datetime.datetime,type(None)):
            if type(date) == datetime.datetime:
                date = date.date()
            return date
        #If it's a string, turn it into a datetime
        elif isinstance(date,str):
            try:
                date_obj = datetime.datetime.strptime(date,self.date_fmt)
                date_obj = date_obj.date()
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
                        dist = act.distance.num
                        time = act.elapsed_time.seconds
                        line = "%s,%s,%s\n"%(date.date(),dist,time)
                        runfile.write(line)
                        
    def remove_last_line(self,fname):
        """Remove the last line of a file"""
        if os.path.isfile(fname):
            lines = []
            with open(fname) as f:
                lines = f.readlines()
            with open(fname,'w') as f:
                wlines = lines[:-1]
                f.writelines(wlines)
            return lines[-1]
        else:
            return None
                        
    def update_db(self,date,over_write = False):
        """Get new data from and add to db"""
        date = self._set_date_(date)
        if date:
            date = date + datetime.timedelta(days = 1) #Dont repeat the last line
            
        if os.path.isfile(DB_CAL) and date: 
            cdate = date.date()
            last = "any string"
            if over_write:
                cdate = cdate - datetime.timedelta(days = 1)
                last = self.remove_last_line(DB_CAL)
            if last:
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
                        print line
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
                        dist = act.distance.num
                        time = act.elapsed_time.seconds
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
        
    def readfile(self,fname):
        """Read file into np array. Returns list of columns."""
        if os.path.isfile(fname):
            try:
                data = np.genfromtxt(fname,dtype = str, delimiter = ',')
            except:
                return []
            numcols = data.shape[-1]
            try:
                date = np.array([self._set_date_(d) for d in data[:,0]])
            except:
                date = None
            
            return_list = []
            return_list.append(date)
            for i in range(1,numcols):
                col = data[:,i]
                col = np.array([float(num) for num in col])
                return_list.append(col)
            
            return return_list
        
        else:
            print "DB info not found."
            return None
    
    def get_calorie_data(self,date = None,binsize = 1):
        """Get calorie info for a given date. If no date is provided,
        self.start and self.stop are used as bounds, and arrays are returned."""
        if date:
            date = self._set_date_(date)
            if date:
                date = datetime.datetime.combine(date,time)
                mask = [self._caldate <= date]
                cals = self._calcons[mask]
                goal = self._calgoal[mask]
                
                if cals.size and goal.size:
                    return_cals = cals[-1]
                    return_goal = goal[-1]
                    return date,return_cals,return_goal
                else:
                    return None,None,None
            else:
                return None,None,None
        
        else:
            if self.start_date == None:
                start = datetime.date(1,1,1)
            else:
                start = self.start_date
            
            if self.stop_date == None:
                stop = datetime.date(2100,1,1)
            else:
                stop = self.stop_date
            
            mask = [(self._caldate >= start) & (self._caldate <= stop)]
            dates = self._caldate[mask]
            cals = self._calcons[mask]
            goal = self._calgoal[mask]
            
            #Now bin the data
            if binsize>=1 and cals.size:
                bindates,cals = self.binned(dates,cals,binsize)
                bindates,goal = self.binned(dates,goal,binsize)
                return bindates,cals,goal
            else:
                print "Binsize must be >= 1."
                return None,None,None
    
    def get_weight_data(self,date = None,binsize = 1):
        """Get weight info for a given date (see get_calorie_info)"""
        if date:
            date = self._set_date_(date)
            if date:
                mask = [self._wtdate <= date]
                wt = self._wt[mask]
                
                if wt.size:
                    return_wt = wt[wt>0][-1]
                    dt = self._wtdate[mask][-1]
                    return dt,return_wt
                else:
                    return None,None
            else:
                return None,None
        
        else:
            if self.start_date == None:
                start = datetime.date(1,1,1)
            else:
                start = self.start_date
            
            if self.stop_date == None:
                stop = datetime.date(2100,1,1)
            else:
                stop = self.stop_date
            
            mask = [(self._wtdate >= start) & (self._wtdate <= stop)]
            dates = self._wtdate[mask]
            wt = self._wt[mask]
            
            #Now bin the data
            if binsize>=1 and wt.size:
                bindates,wt = self.binned(dates,wt,binsize)
                return bindates,wt
            else:
                print "Binsize must be >= 1."
                return None,None
            
    def get_run_data(self,date = None,binsize = 1):
        """Get data from runs"""
        if date:
            date = self._set_date_(date)
            if date:
                mask = [self._rundate <= date]
                dist = self._rundist[mask]
                time = self._runtime[mask]
                
                if dist.size and time.size:
                    return_dist = dist[dist>0][-1]
                    return_time = time[dist>0][-1]
                    return date,return_dist,return_time
                else:
                    return None,None,None
            else:
                return None,None,None
        
        else:
            if self.start_date == None:
                start = datetime.date(1,1,1)
            else:
                start = self.start_date
            
            if self.stop_date == None:
                stop = datetime.date(2100,1,1)
            else:
                stop = self.stop_date
            
            mask = [(self._rundate >= start) & (self._rundate <= stop)]
            dates = self._rundate[mask]
            dist = self._rundist[mask]
            time = self._runtime[mask]
            
            #Now bin the data
            if binsize>=1 and dist.size:
                bindates,dist = self.binned(dates,dist,binsize)
                bindates,time = self.binned(dates,time,binsize)
                return bindates,dist,time
            else:
                print "Binsize must be >=1."
                return None,None,None
            
    def BMI(self,wt):
        wt = float(wt)
        ht = float(self.height)
        bmi = 703 * wt / ht**2
        return bmi
    
    def weight_from_BMI(self,bmi):
        bmi = float(bmi)
        ht = float(self.height)
        wt = bmi * ht**2 / 703
        return wt
            
        
    def binned(self,x,y,binsize,xdates = True,avg = False):
        """Take x and y data and bin them into 'binsize' size bins."""
        #If x axis are date objects
        binsize = float(binsize)
        if xdates:
            #Define the x axis bins
            dayspan = (x[-1] - x[0]).days + binsize
            bincenters = np.arange(0., dayspan, binsize)
            bincenters_dates = np.array([x[0] + datetime.timedelta(days = b) for b in bincenters])
            data = np.zeros_like(bincenters)
            
            for i in range(data.size):
                left = bincenters_dates[i] - datetime.timedelta(days = binsize / 2)
                right = bincenters_dates[i] + datetime.timedelta(days = binsize /2)
                
                mask = [(x>=left) & (x<=right)]
                datamsk = y[mask]
                
                if avg:
                    data[i] = datamsk.mean()
                else:
                    data[i] = datamsk.sum()
                
            return bincenters_dates,data
                
    def weight_slope(self):
        """Linear fit to weight"""
        date,wt = self.get_weight_data()
        mask = [wt > 0]
        date = date[mask]
        wt = wt[mask]
        
        if wt.size > 1:
            days = (date[-1] - date[0]).days
            wt_diff = wt[-1] - wt[0]
            slope = wt_diff / days
            return slope
        else:
            return None
    
    def projected_weight(self,date):
        """At current pace what will my weight be by 'date'"""
        date = self._set_date_(date)
        if date:
            if type(date) == datetime.datetime:
                today = datetime.datetime.today()
            if type(date) == datetime.date:
                today = datetime.date.today()
            
            dt,cur_wt = self.get_weight_data(today)
            days = (date - dt).days
            slope = self.weight_slope()
            if slope:
                proj_wt = cur_wt + slope * days
                return proj_wt
            else:
                print "Not enough data."
                return None
        else:
            return None
    
    def projected_date(self,weight):
        """At current pace what day will my weight be 'weight'"""
        #current wt + slope * ? = weight
        #? = (weight - current wt ) / slope
        dt,cur_wt = self.get_weight_data(datetime.date.today())
        slope = self.weight_slope()
        if slope:
            days = (weight - cur_wt) / slope
            date = dt + datetime.timedelta(days = days)
            return date
        else:
            print "Not enough data."
            return None
        
    def print_weight_summary(self):
        """Print a summary"""
        BMI_DICT = {"Overweight":self.weight_from_BMI(30.),"Healthy":self.weight_from_BMI(25.)}
        today = datetime.date.today()
        last_meas,current_wt = self.get_weight_data(today)
        if current_wt:
            current_bmi = self.BMI(current_wt)
            slope = self.weight_slope()
            
            print "As of %s, you weigh %.1f lbs (BMI = %.1f)."%(last_meas,current_wt,current_bmi)
            
            if current_wt >= BMI_DICT['Overweight']:
                print "You are currently obese."
            elif current_wt < BMI_DICT['Overweight'] and current_wt >= BMI_DICT['Healthy']:
                print "You are currently overweight."
            else:
                print "You are currently at a healthy weight."
            
            if slope:
                print "You are losing %.1f lbs per week."%(slope * -7)
                
            for key in sorted(BMI_DICT.keys(),reverse = True):
                wt = BMI_DICT[key]
                if current_wt > wt:
                    wtdate = self.projected_date(wt)
                    print "You will weigh %.1f (%s) by %s."%(wt,key.lower(),wtdate)
            
        
            
    
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
        
                
        