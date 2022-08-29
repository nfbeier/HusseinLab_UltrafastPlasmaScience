---
description: >-
  Code for receiving serially communicated messages and passing commands to the
  stepper driver. Program automatically runs on the Lab's Pi startup.
---

# uart\_receiver.py

The following sets up serial communication. Port should stay the same for all newer Raspberry Pis.

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
# pause time between motor pulses.
pulse_delay = 0.0005 
 
# stepwindow size, how many steps are taken between consecutive measurements: 
# 200 steps = 1 full rotation = 1mm
mm_step = 200  
```
{% endcode %}

The GPIO connections are dependant on your wiring to a stepper driver or are dependant on the stepper driver hat you are using. Change the following according to your system specifications.

```python
while True:
    while ser.in_waiting:  # Keeps serial on standby when nothing is being received
        GPIO.setmode(GPIO.BCM)

        # CHANGE STARTING HERE
        # x-axis
        GPIO.setup(13, GPIO.OUT)  # direction
        GPIO.setup(19, GPIO.OUT)  # step
        GPIO.setup(12, GPIO.OUT)  # enable

        # y-axis
        GPIO.setup(24, GPIO.OUT)  # direction
        GPIO.setup(18, GPIO.OUT)  # step
        GPIO.setup(4, GPIO.OUT)  # enable
```

The rest of the code reads in messages and decodes them to command the motor.&#x20;

* All messages are composed of a string of 6 numbers. The first two numbers denote the gpio pin to command and the next four numbers denote the parameter.
* If the gpio is a direction pin (ie. 13 or 24), then a parameter of 0001 refers to forward motion and 0000 refers to reverse motion.
  * ex. 130001 means to command the x-axis motor to move in the forward direction.
* If the gpio is a step pin (ie. 19 or 18), then the parameter is the length (mm) of the step to take.
  * ex. 180010 means to move the y-axis motor by 10 mm.
* At the start of every message sent and when the commands are done executing, the motor will enable/disable itself so to keep the motors from overheating.
