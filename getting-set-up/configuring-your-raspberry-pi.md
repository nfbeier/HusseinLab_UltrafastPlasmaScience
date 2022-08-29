---
description: 'THIS IS OPTIONAL: ONLY DO IF RUNNING LIBS GUI WITH A STAGE'
---

# Configuring Your Raspberry Pi

## Connecting to a Raspberry Pi

{% tabs %}
{% tab title="VNC" %}
VNC is auto-installed on Raspberry Pi OS and only needs to be enabled. Similar to Remote Desktop, VNC gives access to the entire desktop display. It is pretty slow though.

{% embed url="https://www.realvnc.com/en/raspberrypi/" %}
{% endtab %}

{% tab title="SSH" %}
SSH gives access to the Pi through only the terminal.&#x20;

Note: if you're trying to develop on UAlberta campus grounds, SSH won't work through UWS wifi due to the school's security measures. If you really want to SSH at school though, contact Steven Knudsen.

{% embed url="https://www.howtogeek.com/768053/how-to-ssh-into-your-raspberry-pi/" %}



I like to use Visual Studio Code to develop since I can remotely edit the Pi's code through the VS IDE.

{% embed url="https://code.visualstudio.com/docs/remote/ssh" %}
Instructions to remotely develop using Vistual Studio Code and SSH.
{% endembed %}
{% endtab %}

{% tab title="Wired" %}
The Pi comes equipped with a micro-HDMI port that can be used to connect to a monitor with HDMI.
{% endtab %}
{% endtabs %}

## Serial Communication

The Pi needs to be connected to a computer (that will run LIBS GUI) through a serial to USB converter.&#x20;

![](<../.gitbook/assets/Serial to USB Diagram>)

After connecting the Pi to the computer, go into stage\_control.py and edit line "port='COM11'". Replace COM11 with the port that the USB to serial converter is plugged into.

<pre class="language-python"><code class="lang-python"><strong>ser = serial.Serial(
</strong>        port = 'COM11', 
        baudrate = 115200, 
        timeout = 0.050
        )</code></pre>

## Stepper Driver Connections

![GPIO connections for the stepper driver I used. Note: there is a typo, "A3A4B3B4 Dir" is actually "A3A4B3B4 enable".](<../.gitbook/assets/Stepper Driver to GPIO pins>)

The above are the GPIO pins that correspond to the stepper driver pins I used. If yours are different, see [uart\_receiver.py.md](../code-overview/uart\_receiver.py.md "mention") for where to edit the code.

## Running uart\_receiver.py

Clone the repository onto the Pi (see [installation-configuration.md](installation-configuration.md "mention")) and change directories into the LIBS with stage folder:

```
cd ./HusseinLab_UltrafastPlasmaScience/LIBS_withStage
```

Then run the code:

```
python3 uart_receiver.py
```

The uart\_receiver.py code will need to be re-ran every time you want to run LIBS\_withStage/LIBS\_GUI.py

Another option is to have the Pi run the code automatically on startup.&#x20;

{% embed url="https://www.dexterindustries.com/howto/run-a-program-on-your-raspberry-pi-at-startup/" %}
