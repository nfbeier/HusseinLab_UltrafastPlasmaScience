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

Because I was unable to generalize the code into variables

```python

        gpio = ser.read(2).decode("ascii")
        para = ser.read(4).decode("ascii")
        
        if gpio == '13':  # Direction
            GPIO.output(12, 1)
            if para == '0001':
            	GPIO.output(13, 1)
            elif para == '0000':
                GPIO.output(13, 0)
        elif gpio == '24':
            GPIO.output(4, 1)
            if para == '0001':
            	GPIO.output(24, 1)
            elif para == '0000':
                GPIO.output(24, 0)

        elif gpio == '19':  # Step
            for i in range(int(float(para) * 200)):
                GPIO.output(19, 0)
                time.sleep(pulse_delay)
                GPIO.output(19, 1)
                time.sleep(pulse_delay)
            GPIO.output(12, 0)
            GPIO.cleanup()
        elif gpio == '18':
            for i in range(int(float(para) * 200)):
                GPIO.output(18, 0) #18
                time.sleep(pulse_delay)
                GPIO.output(18, 1)
                time.sleep(pulse_delay)
            GPIO.output(4, 0)
            GPIO.cleanup()
```
