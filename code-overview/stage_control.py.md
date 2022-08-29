---
description: >-
  Program for sending UART serial messages to the Raspberry Pi in order to
  control the two stepper motors.
---

# stage\_control.py

The following sets up serial communication. The line with "port" should be changed if the USB is ever moved.

```python
ser = serial.Serial(
        port = 'COM11', 
        baudrate = 115200, 
        timeout = 0.050
        )
```

<details>

<summary>class Motor:<br><em>contains methods of controlling direction and step delays of stepper motor</em></summary>

**Attributes:**\
&#x20;   • min (int vector) : Start stop limit.\
&#x20;   • max (int vector) : End stop limit.\
&#x20;   • dir (int vector) : Direction to move motor in. 1 for forward and 0 for reverse.\
&#x20;   • coord (float vector) : Coordinate location of stage in mm.\
&#x20;   • home (float vector) : Coordinate location of home.\
&#x20;   • gpio\_dir (int vector) : GPIO pins corresponding to x and y direction, respectively.\
&#x20;   • gpio\_step (int vector) : GPIO pins corresponding to x and y step, respectively.\
&#x20;   __    \
_Note: edit gpio\_dir and gpio\_step if using different connections._\
_Note: in all size 2 vectors, the first number (index 0) is for the x-axis and the second number (index 1) is for y_

**set\_dir**\
Sets direction value and configures the motor to travel in set direction.\
Parameters:\
&#x20;   • dir (int vector) : Direction of travel. 1 for forward and 0 or reverse.\
&#x20;   • axis (int) : The axis being manipulated. 0 for x and 1 for y.

**update\_coord**\
****Counts the number of steps taken to get the new absolute location of stage.\
Parameters:\
&#x20;   • dist (float) : Distance (in mm) of the step taken.\
&#x20;   • axis (int) : Indexes into a list where 0 is the x-axis and 1 is the y-axis.

**step\_dist**\
Communicates with the Raspberry Pi (via serial communication) to take a step of length mm\_dist in direction dir.\
Parameters:\
&#x20;   • mm\_dist (float) : Distance in mm of the desired step\
&#x20;   • dir (int) : Direction of travel. 0 for reverse and 1 for forward.\
&#x20;   • axis (int) : Indexes into a list where 0 is the x-axis and 1 is the y-axis.

</details>

<details>

<summary>class Control:<br><em>subclass of Motor that contains methods of commanding the motor to move in specialized ways</em></summary>

**left**\
Takes a step of length 1 mm left (reverse in the x-axis).\
Parameters:\
&#x20;   • inst : Instance of the Motor class\
&#x20;   • dist (float) : Distance of travel.

**right**\
Takes a step of length 1 mm right (forward __ in the x-axis). \
Parameters:\
&#x20;   • inst : Instance of the Motor class\
&#x20;   • dist (float) : Distance of travel.

**up**\
Takes a step of length 1 mm up (reverse in the y-axis). \
Parameters:\
&#x20;   • inst : Instance of the Motor class\
&#x20;   • dist (float) : Distance of travel.

**down**\
Takes a step of length 1 mm down (reverse __ in the y-axis). \
Parameters:\
&#x20;   • inst : Instance of the Motor class\
&#x20;   • dist (float) : Distance of travel.

**return\_home**\
Calculates distance from the stage's current location to home. Then moves to home based on distance.\
Parameters:\
&#x20;   • inst: Instance of the Motor class.

</details>
