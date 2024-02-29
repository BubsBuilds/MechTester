#!/usr/bin/env python3
from datetime import datetime

from nicegui import app, run, ui
import csv
import gpiozero
import pymongo
import time

class dbComm:
    def __init__(self, host="JFS-MAIN", port=27017, db_name='mt'):
        self.client = pymongo.MongoClient(host, port)
        self.db = self.client[db_name]


class lcComm:

    def __init__(self):
        self.active = True
        self.lc_const = 2940 / 4194304
        self.lc_offset = 0
        self.DT_PIN = 10
        self.SCK_PIN = 22
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

def setMotors(dir, val):
    pass

def updateLinePlot():
    try:
        lcPlot.push([lcSess.times], [[lcSess.vals]])
        lcVal.set_text(str(lcSess.curLCval))
    except:
        pass

def callGetLC():
    lcSess.getLC()


async def startup(db, lc):
    global dbSess
    global lcSess
    dbSess = db
    lcSess = lc
    lcSess.initdb(dbSess)
    ui.dark_mode().enable()
    result = await run.cpu_bound(callGetLC)


app.on_startup(startup(dbComm(), lcComm()))

ui.label('Mech Tester').classes('text-h1')
ui.separator()
with ui.column():
    with ui.card():
        ui.label('Manual Actuator Controls')
        ui.separator()
        motorSpeed = ui.slider(min=0, max=100, value=80)
        ui.label().bind_text_from(motorSpeed, 'value')
        ui.button('UP', on_click=lambda: setMotors(1, motorSpeed.value))
        ui.button('DOWN', on_click=lambda: setMotors(-1, motorSpeed.value))

    with ui.card():
        ui.label('Load Cell')
        ui.separator()
        lcVal = ui.label('0')
        # lcVal = ui.label().classes('text-h3').bind_text(target_object= getLC, target_name='curLCval')
        lcPlot = ui.line_plot(n=1, limit=100, figsize=(10, 5), update_every=5, close=False)
        ui.button('TARE', on_click=lambda: lcSess.tare)
try:
    line_updates = ui.timer(0.5, updateLinePlot, active=True)
except:
    pass
# ui.button('Stop LC', on_click=lambda getLCstat: False)

ui.run(reload=False)
