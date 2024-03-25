#!/usr/bin/env python3
from datetime import datetime

from nicegui import app, run, ui
import csv
from datetime import datetime
import json
import pymongo
import serial
import time

class dbComm:
    def __init__(self, host="JFS-MAIN", port=27017, db_name='mt'):
        self.client = pymongo.MongoClient(host, port)
        self.db = self.client[db_name]

class mechController:
    def __init__(self, serial_port='/dev/ttyUSB0', baud_rate=9600):
        self.ser = serial.Serial(serial_port, baud_rate)
        self.log_file = "command_log.json"
        self.commands_log = []
        self.lcCal = 2940 / 4194304
        time.sleep(2)

    def send_command(self, command):
        self.ser.write(command.encode())
        time.sleep(0.1)
        confirmation = self.ser.readline().decode().strip()
        self.log_command(command, confirmation)
        return confirmation

    def log_command(self, command, confirmation):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = {"timestamp": timestamp, "command": command, "confirmation": confirmation}
        self.commands_log.append(log_entry)
        with open(self.log_file, 'w') as file:
            json.dump(self.commands_log, file, indent=4)

    def set_motor(self, motor, direction, speed):
        speed = round(speed / 100 * 255)
        command = f"M{motor}{direction}{speed}\n"
        self.send_command(command)

    def read_scale(self):
        newVal = float(self.send_command("HXREAD\n").split(" ")[1])
        newVal = newVal * self.lcCal
        curTime = time.time()
        return newVal, curTime

    def tare_scale(self):
        self.send_command("HXTARE\n")

    def close(self):
        self.ser.close()

def updateLinePlot(mc):
    newVal, curTime = mc.read_scale()
    lcVals.append(newVal)
    lcTimes.append(curTime)
    lcPlot.push([lcTimes], [[lcVals]])
    lcVal.set_text(str(newVal))


async def startup(db, mc):
    global dbSess
    global mcSess
    global lcVals
    global lcTimes
    dbSess = db
    mcSess = mc
    lcVals = []
    lcTimes = []
    ui.dark_mode().enable()

app.on_startup(startup(dbComm(), mechController()))

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
        calVal = ui.label(str(2940 / 4194304))
try:
    line_updates = ui.timer(0.5, updateLinePlot(mcSess), active=True)
except:
    pass
# ui.button('Stop LC', on_click=lambda getLCstat: False)

ui.run()
