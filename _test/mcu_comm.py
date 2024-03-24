import serial
import time
import json
from datetime import datetime


class RobotController:
    def __init__(self, serial_port='/dev/ttyUSB0', baud_rate=9600):
        self.ser = serial.Serial(serial_port, baud_rate)
        self.log_file = "command_log.json"
        self.commands_log = []
        time.sleep(2)

    def send_command(self, command):
        self.ser.write(command.encode())
        confirmation = self.ser.readline().decode().strip()
        self.log_command(command, confirmation)

    def log_command(self, command, confirmation):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = {"timestamp": timestamp, "command": command, "confirmation": confirmation}
        self.commands_log.append(log_entry)
        with open(self.log_file, 'w') as file:
            json.dump(self.commands_log, file, indent=4)

    def set_motor(self, motor, direction, speed):
        command = f"M{motor}{direction}{speed}\n"
        self.send_command(command)

    def read_scale(self):
        self.send_command("HXREAD\n")

    def tare_scale(self):
        self.send_command("HXTARE\n")

    def close(self):
        self.ser.close()


if __name__ == "__main__":
    controller = RobotController()

    # Example usage
    controller.set_motor('A', 'F', 255)
    time.sleep(2)
    controller.set_motor('A', 'F', 0)

    controller.tare_scale()
    time.sleep(1)
    controller.read_scale()

    controller.close()
