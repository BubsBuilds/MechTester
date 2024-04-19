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
    def __init__(self, host="192.168.50.41", port=27017, db_name='mt'):
        self.client = pymongo.MongoClient(host, port)
        self.db = self.client[db_name]
        self.dbSessColl = self.db['mt_sess']
        self.datColl = self.db['lt_dat']
        self.ltParamColl = self.db['lt_params']
        # Create document for session data
        self.sessHead = {
            'ts': time.time(),
            'data_recs': [],
        }
        self.sessRecID = self.dbSessColl.insert_one(self.sessHead).inserted_id

class mechController:
    def __init__(self, serial_port='/dev/ttyACM0', baud_rate=9600):
        self.ser = serial.Serial(serial_port, baud_rate)
        self.log_file = "command_log.json"
        self.dbSess = dbComm()
        self.commands_log = []
        self.dt_jog = .1
        self.lcCal = 2940 / 4194304
        self.lcVals = []
        self.lcTimes = []
        self.lcVal = 0
        self.lcTime = time.time()
        time.sleep(2)

    def send_command(self, command):
        self.ser.write(command.encode())
        time.sleep(0.2)
        confirmation = self.ser.readline().decode().strip()
        retList = self.parse_command(confirmation)
        self.log_command(command, confirmation)
        return retList

    def parse_command(self, message):
        # Remove the leading and trailing characters ('<<' and '>>')
        #cleaned_string = message.strip("<<>>")
        cleaned_string = message.split("<<")[1]
        cleaned_string = cleaned_string.split(">>")[0]
        # Split the cleaned string by '><' to separate id and value
        id_value_list = cleaned_string.split("><")

        # Return the list in the desired format
        return id_value_list

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
        time.sleep(self.dt_jog)
        self.send_command(f"MAS0\n")

    def read_scale(self):
        ret = self.send_command("HXREAD\n")
        newVal = float(ret[1])
        self.lcVal = newVal * self.lcCal
        self.lcTime = time.time()
        self.lcVals.append(self.lcVal)
        self.lcTimes.append(self.lcTime)

    def tare_scale(self):
        self.send_command("HXTARE\n")

    def load_test(self, test_name, test_desc, test_part, test_type, test_limit):
        if test_type == 1:
            test_type = "C"
        elif test_type == 2:
            test_type = "T"
        i = 0
        extras = 50
        #Set up load test records
        param_rec = {
            'start_time': time.time(),
            'end_time': time.time(),
            'name': test_name,
            'desc': test_desc,
            'part_name': test_part,
            'type': test_type,
            'load_limit': test_limit,
            'lc_cal': self.lcCal,
        }
        dat_rec = {
            'load_times': [],
            'disp_times': [],
            'loads': [],
            'disps': [],
        }
        runL = True

        self.send_command(f"CL{test_type}{round(test_limit * self.lcCal)}\n")
        while runL or i <= extras:
            if self.ser.in_waiting:
                response = self.ser.readline().decode()
                parsed = self.parse_command(response)
                if parsed[0] == 'lc':
                    dat_rec['load_times'].append(time.time())
                    load = float(parsed[1]) * self.lcCal
                    self.lcVal = load
                    self.lcVals.append(load)
                    self.lcTimes.append(time.time())
                    dat_rec['loads'].append(load)
                elif parsed[0] == 'ds':
                    dat_rec['disp_times'].append(time.time())
                    dat_rec['disps'].append(float(parsed[1]))
                elif parsed[0] == 'lt':
                    param_rec['end_time'] = time.time()
                    runL = False
                else:
                    print(f"Command error. Response received: {response}")
            if not runL:
                parsed = self.send_command(f"HXALL\n")
                i += 1
                if parsed[0] == 'lc':
                    dat_rec['load_times'].append(time.time())
                    load = float(parsed[1]) * self.lcCal
                    self.lcVal = load
                    self.lcVals.append(load)
                    self.lcTimes.append(time.time())
                    dat_rec['loads'].append(load)
                elif parsed[0] == 'ds':
                    dat_rec['disp_times'].append(time.time())
                    dat_rec['disps'].append(float(parsed[1]))
                else:
                    print(f"Command error. Parsed received: {parsed}")
        param_rec_id = self.dbSess.ltParamColl.insert_one(param_rec).inserted_id
        print(f"Parameters recorded at: {param_rec_id}")
        dat_rec_id = self.dbSess.datColl.insert_one(dat_rec).inserted_id
        print(f"Data recorded at: {dat_rec_id}")
        return [param_rec_id, dat_rec_id]

    def get_lc(self):
        return self.lcVal

    def close(self):
        self.ser.close()

def updateLinePlot(mcSess):
    #mcSess.read_scale()
    #time.sleep(0.2)
    try:
        lcPlot.push(mcSess.lcTimes, [mcSess.lcVals])
        lcVal.set_text(str(mcSess.lcVal))
    except:
        pass

async def startup():
    ui.dark_mode().enable()

async def run_test(mcSessp, lt_name, lt_desc, lt_part, lt_type, lt_limit):
    result = await run.cpu_bound(mcSessp.load_test(lt_name, lt_desc, lt_part, lt_type, lt_limit))
    ui.notify(f'Test Completed at {time.time()}')

#dbSess = dbComm()
mcSess = mechController()
app.on_startup(startup())

ui.label('Mech Tester').classes('text-h1')
ui.separator()
with ui.column():
    with ui.card():
        ui.label('Manual Actuator Controls')
        ui.separator()
        motorSpeed = ui.slider(min=0, max=100, value=80)
        ui.label().bind_text_from(motorSpeed, 'value')
        ui.button('UP', on_click=lambda: mcSess.set_motor('A', 'R', int(motorSpeed.value)))
        ui.button('DOWN', on_click=lambda: mcSess.set_motor('A', 'F', int(motorSpeed.value)))
        ui.button('STOP', on_click=lambda: mcSess.set_motor('A','F', int(0)))
        ui.separator()
        lt_name = ui.input(placeholder='Test Name').props('rounded outlined dense')
        lt_part = ui.input(placeholder='Part Name').props('rounded outlined dense')
        lt_desc = ui.textarea(value='Test Description').props('clearable')
        lt_type = ui.radio({1: 'Compression', 2: 'Tension'}, value=1).props('inline')
        lt_limit = ui.slider(min=-500, max=500, value=0)
        ui.label().bind_text_from(lt_limit, 'value')
        ui.button('RUN', on_click=lambda: run_test(mcSess, lt_name.value, lt_desc.value, lt_part.value, lt_type.value, lt_limit.value))

    with ui.card():
        ui.label('Load Cell')
        ui.separator()
        lcVal = ui.label('0')
        # lcVal = ui.label().classes('text-h3').bind_text(target_object= getLC, target_name='curLCval')
        lcPlot = ui.line_plot(n=1, limit=100, figsize=(10, 5), update_every=1, close=False)
        ui.button('TARE', on_click=lambda: mcSess.tare_scale())
        calVal = ui.label(str(2940 / 4194304))
line_updates = ui.timer(0.5, lambda: updateLinePlot(mcSess), active=True)

ui.run(reload=True)
