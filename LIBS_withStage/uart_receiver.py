# Code for receiving serially communcated messages. Program automatically runs on the Lab's Pi startup.

import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
# x-axis
dir_x = GPIO.setup(13, GPIO.OUT)
step_x = GPIO.setup(19, GPIO.OUT)
mode_x = GPIO.setup((16, 17, 20), GPIO.OUT) 
# y-axis
dir_y = GPIO.setup(24, GPIO.OUT)
step_y = GPIO.setup(18, GPIO.OUT)
mode_y = GPIO.setup((21, 22, 27), GPIO.OUT) 

import serial, time
ser = serial.Serial(
        port = '/dev/serial0', 
        baudrate = 115200, 
        timeout=0.050
        )

pulse_delay = 0.0005  # pause time between motor pulses. Note: 0.0005 seems to be the minimum for chosen motor/driver.
mm_step = 200  # stepwindow size, how many steps are taken between consecutive measurements: 200 steps = 1 full rotation = 1mm
GPIO.output(mode_x, (0, 0, 1))  # 1/16 microstepping
GPIO.output(mode_y, (0, 0, 1))


while True:
    while ser.in_waiting:  # Keeps serial on standby when nothing is being received
        gpio = int(ser.read(2).decode("ascii"))
        para = int(ser.read(4).decode("ascii"))

        if gpio == 13 or gpio == 24:  # Direction
            GPIO.output(gpio, para)  # para = 1 for forward and para = 0 for reverse
    
        elif gpio == 19 or gpio == 18:  # Step
            for i in range(para * 200):
                GPIO.output(gpio, 0)
                time.sleep(pulse_delay)
                GPIO.output(gpio, 1)
                time.sleep(pulse_delay) 