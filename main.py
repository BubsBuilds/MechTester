#!/usr/bin/env python3
from datetime import datetime

from nicegui import run, ui
import csv
import gpiozero
import pymongo
import time

class dbComm:
  def __init__(self, host="JFS-MAIN", port=27017, db_name='mt'):
    self.client = pymongo.MongoClient(host, port)
    self.db = self.client[db_name]

class lcComm:
  def __init__(self, dbComm):
    self.lc_const = 2940 / 4194304
    self.lc_offset = 0
    self.DT_PIN = 10
    self.SCK_PIN = 22
    self.sck = gpiozero.OutputDevice(self.SCK_PIN)
    self.dt = gpiozero.InputDevice(self.DT_PIN)
    self.vals = []
    self.times = []
    self.dbComm = dbComm
    # Create document for session data
    rec = {
      'time': time.time(),
      'lcDat': [],
    }
    self.coll = self.dbComm.db['test_data']
    self.datRec = self.coll.insert_one(rec).inserted_id
  def getLC(self):
    try:
      while getLCstat == 'ON':
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
        self.curLCval = round(float(signed_data * self.lc_const), 3)  - self.lc_offset
        self.curTime = round(time.time(), 3)
        self.coll.update_one({'_id': self.datRec}, {'$push': [self.curTime, self.curLCval]})
        time.sleep(0.2)
        #print(load)
    except:
      print('Get LC Fail')

  def tare(self):
    self.lc_offset = self.curLCval

    outfilepath = f'./TestResult_{round(time.time())}.csv'
    with open(outfilepath, 'w', newline='') as file:
      writer = csv.writer(file)
      for i, load in enumerate(vals):
        writer.writerow([times[i], load])
def setMotors(dir, val):
  pass
#
# async def LoadCellDatLoop():
#   pass

async def lcGetter():
  result = await run.cpu_bound(lcComm.getLC())

def updateLinePlot() -> None:
  lcPlot.push([lcComm.curTime], [[lcComm.curLCval]])
  lcVal.set_text(str(lcComm.curLCval))

dbComm = dbComm()
lcComm = lcComm(dbComm)
getLCstat = ui.label('ON')
curLCval = 0
ui.dark_mode().enable()
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
    #lcVal = ui.label().classes('text-h3').bind_text(target_object= getLC, target_name='curLCval')
    lcPlot = ui.line_plot(n=1, limit=100, figsize=(15, 10), update_every=1)
    ui.button('TARE', on_click=lambda: lcComm.tare)

ui.button('Stop LC', on_click=lambda getLCstat: False )



ui.run()