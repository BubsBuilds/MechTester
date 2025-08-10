from datetime import datetime

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
        print(f'Session record created at: {self.sessRecID}')

class mechController:
    def __init__(self, serial_port='COM6', baud_rate=115200):
        self.ser = serial.Serial(serial_port, baud_rate)
        self.log_file = "command_log.json"
        self.dbSess = dbComm()
        self.commands_log = []
        self.dt_jog = .05
        self.lcCal = -2940 / 4194304
        self.lcVals = []
        self.lcTimes = []
        self.lcVal = 0
        self.lcTime = time.time()
        self.ltCycles = 1
        #time.sleep(1)

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
    #def response_handler(self, retList):


    def log_command(self, command, confirmation):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = {"timestamp": timestamp, "command": command, "confirmation": confirmation}
        self.commands_log.append(log_entry)
        with open(self.log_file, 'w') as file:
            json.dump(self.commands_log, file, indent=4)

    def set_motor(self, motor, load_direction, speed):
        speed = round(speed / 100 * 255)
        command = f"M{motor}{load_direction}{speed}\n"
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
        return newVal

    def tare_scale(self):
        self.send_command("HXTARE\n")
        #time.sleep()

    def load_test(self, test_name, test_desc, test_part, test_type, test_limit):
        if test_type == 1:
            test_type = "C"
        elif test_type == 2:
            test_type = "T"
        loop_count = 0
        cur_limit = test_limit
        load_dir = "load"
        param_rec = {
            'start_time': time.time(),
            'end_time': time.time(),
            'name': test_name,
            'desc': test_desc,
            'part_name': test_part,
            'type': test_type,
            'load_limit': test_limit,
            'lc_cal': self.lcCal,
            'load_direction': load_dir,
        }
        param_rec_id = self.dbSess.ltParamColl.insert_one(param_rec).inserted_id
        print(f"Parameters recorded at: {param_rec_id}")
        time.sleep(2)
        self.tare_scale()
        time.sleep(2)
        while loop_count <= self.ltCycles:
            i = 0
            extras = 50
            # Start by taring the load cell

            #Set up load test record

            dat_rec = {
                'load_times': [],
                'disp_times': [],
                'loads': [],
                'disps': [],
                'load_direction': load_dir,
                'param_rec_id': param_rec_id,
            }
            runL = True
            self.send_command(f"CL{test_type}{round(cur_limit / self.lcCal)}\n")
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
                        print(f"Current load: {load}")
                        dat_rec['loads'].append(load)
                    elif parsed[0] == 'ds':
                        dat_rec['disp_times'].append(time.time())
                        dat_rec['disps'].append(float(parsed[1]))
                        print(f"Current Disp: {float(parsed[1])}")
                    elif parsed[0] == 'lt':
                        param_rec['end_time'] = time.time()
                        if load_dir == "unload":
                            if test_type == "T":
                                self.set_motor("A", "R", 75)
                                time.sleep(0.02)
                                self.set_motor("A", "S", 0)
                        runL = False
                    else:
                        #print(f"Command error. Response received: {response}")
                        pass
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

            dat_rec_id = self.dbSess.datColl.insert_one(dat_rec).inserted_id
            print(f"Data recorded at: {dat_rec_id}")

            if test_type == "C":
                test_type = "T"
            elif test_type == "T":
                test_type = "C"
            if load_dir == "load":
                load_dir = "unload"
                cur_limit = 0
                loop_count += 1
            elif load_dir == "unload":
                load_dir = "load"
                cur_limit = test_limit
        return [param_rec_id, dat_rec_id]

    def get_lc(self):
        return self.lcVal

    def close(self):
        self.ser.close()

if __name__ == "__main__":
    mc_sess = mechController()
    ret = mc_sess.read_scale()
    print(ret)
    mc_sess.close()