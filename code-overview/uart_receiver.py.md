---
description: >-
  Code for receiving serially communicated messages and passing commands to the
  stepper driver. Program automatically runs on the Lab's Pi startup.
---

# uart\_receiver.py

Required imports:

```python
import RPi.GPIO as GPIO
import serial, time
```

Sets up serial communication. Port should stay the same for all newer Raspberry Pis.

```python
ser = serial.Serial(
        port = '/dev/serial0', 
        baudrate = 115200, 
        timeout=0.050
        )
```

Pulse delay and step window parameters. These are dependent on the motor you have.

{% code overflow="wrap" %}
```python
# pause time between motor pulses. Note: 0.0005 seems to be the minimum for chosen 
# motor/driver.
pulse_delay = 0.0005 
 
# stepwindow size, how many steps are taken between consecutive measurements: 
# 200 steps = 1 full rotation = 1mm
mm_step = 200  
```
{% endcode %}

Reads in messages from the serial line and spilts into two parts (gpio and para/parameter).\
_Ex1. 13001: pin 13 (dir\_x) set to forward_\
_Ex2. 18003: pin 18 (step\__y) _move 3 mm_

```python
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
                time.sleep(pulse_delay)py
```
