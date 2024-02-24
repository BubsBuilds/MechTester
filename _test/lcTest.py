import csv
import gpiozero
import time

# Load Cell parameters
lc_const = 2940 / 4194304

DT_PIN = 10
SCK_PIN = 22
sck = gpiozero.OutputDevice(SCK_PIN)
dt = gpiozero.InputDevice(DT_PIN)
vals = []
times = []
try:
    while True:
        Count = 0
        sck.off()
        #time.sleep(0.001)
        while dt.value == 1:
            time.sleep(0.01)
        for i in range(24):
            start_counter = time.perf_counter()
            sck.on()
            sck.off()
            end_counter = time.perf_counter()
            time_elapsed = float(end_counter - start_counter)
            Count = (Count << 1) | dt.value

        # calculate int from 2's complement
        signed_data = 0
        if (Count & 0x800000):  # 0b1000 0000 0000 0000 0000 0000 check if the sign bit is 1. Negative number.
            signed_data = -((Count ^ 0xffffff) + 1)  # convert from 2's complement to int
        else:  # else do not do anything the value is positive number
            signed_data = Count
        load = signed_data * lc_const
        vals.append(load)
        times.append(time.time())
        time.sleep(0.2)
        print(load)
except KeyboardInterrupt:
    pass

outfilepath = f'./TestResult_{round(time.time())}.csv'
with open(outfilepath, 'w', newline='') as file:
    writer = csv.writer(file)
    for i, load in enumerate(vals):
        writer.writerow([times[i], load])

