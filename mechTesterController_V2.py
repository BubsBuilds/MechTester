#!/usr/bin/env python3
from datetime import datetime

from nicegui import app, run, ui
import csv
import gpiozero
import pymongo
import time

class LCcomms:
    def __init__(self):

        # Static LC vals
        self.samplePeriod = 0.2 # Time required between queries
        self.lc_const = 2940 / 4194304
        self.lc_offset = 0
        self.DT_PIN = 10
        self.SCK_PIN = 22

        # Initialize pins
        self.sck = gpiozero.OutputDevice(self.SCK_PIN)
        time.sleep(0.001)
        self.dt = gpiozero.InputDevice(self.DT_PIN)


        self.vals = []
        self.times = []
        self.curLCval = 0
        self.curTime = time.time()

    def initdb(self, db):
        self.dbComm = db
        # Create document for session data
        rec = {
            'time': time.time(),
            'lcDat': [],
        }
        self.coll = self.dbComm.db['test_data']
        self.datRec = self.coll.insert_one(rec).inserted_id

    def getLC(self):
        # try:
          while self.active:
              Count = 0
              self.sck.off()
              while self.dt.value == 1:
                  time.sleep(0.005)
              for i in range(24):
                  start_counter = time.perf_counter()
                  self.sck.on()
                  self.sck.off()
                  end_counter = time.perf_counter()
                  time_elapsed = float(end_counter - start_counter)
                  Count = (Count << 1) | self.dt.value

              # calculate int from 2's complement
              signed_data = 0
              if (Count & 0x800000):  # 0b1000 0000 0000 0000 0000 0000 check if the sign bit is 1. Negative number.
                  signed_data = -((Count ^ 0xffffff) + 1)  # convert from 2's complement to int
              else:  # else do not do anything the value is positive number
                  signed_data = Count
              self.curLCval = round(float(signed_data * self.lc_const), 3) - self.lc_offset
              self.vals.append(self.curLCval)
              self.curTime = round(time.time(), 3)
              self.times.append(self.curTime)
              self.coll.update_one({'_id': self.datRec}, {'$push': {'lcDat': [self.curTime, self.curLCval]}})
              #lcPlot.push([self.curTime], [[self.curLCval]])
              #lcVal.set_text(str(self.curLCval))
              time.sleep(0.2)
              # print(load)
        # except:
        #     print('Get LC Fail')

    def tare(self):
        self.lc_offset = self.curLCval

class MotorComms:
    def __init__(self):
        # Motor controller static params

        # Init pins
        pass

    def setMotors(dir, val):
        pass

class MechTesterController:
    def __init__(self):
        # Init db and start session record.
        # Configure database
        self.dbclient = pymongo.MongoClient(host="JFS-MAIN", port=27017)
        self.db = self.dbclient['mt']
        self.dbSessColl = self.db['mt_sess']
        # Create document for session data
        rec = {
            'ts': time.time(),
            'settings': {
                "logging": False,
                "limit": 1500,
                "state": "OL",
                "cl_params": {
                    "target": 100,
                    "type": "compression",
                }
            }
        }
        self.sessRecID = self.dbSessColl.insert_one(rec).inserted_id

        # Init Load Cell communication
        lc = LCcomms()

