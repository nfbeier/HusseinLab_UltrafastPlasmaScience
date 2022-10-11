---
description: Issues that gave me a headache
---

# 🤔 Need Help?

## Motor Issues

<details>

<summary>Why is the motor "jammed" (it makes a noise but nothing moves)?</summary>

Unplug the entire system and then ensure the motors are securely plugged into the motor drivers. Sometimes if the connection is loose, it will bug out.

</details>

<details>

<summary>Why aren't the motors rotating?</summary>

1. Make sure the system is plugged in.
2. The Pi takes a few minutes to boot up, try again in a few minutes.
3. Check that messages are being serially communicated. You can do this by VNCing or SSHing onto the Pi (see [configuring-your-raspberry-pi.md](../getting-set-up/configuring-your-raspberry-pi.md "mention")).

</details>

<details>

<summary>Why does only one motor rotate and the other doesn't?</summary>

1. Check that both motors are plugged in.
2. Unplug the whole system and then unplug and replug the motors.

</details>

## Serial Issues

<details>

<summary>Error Message: Don't have permission to read COM11 (or whatever port the Pi is connected through)</summary>

Try unplugging and plugging back in the USB. For whatever reason, this error randomly pops up at times.

</details>

## Other

<details>

<summary>Why does an error message repeatedly print during single shot?</summary>

Something is disconnected. Check that the spectrometers are connected and the delay generator is on.

</details>

<details>

<summary>Why won't it allow me to click the "Single Shot" button?</summary>

Ensure the stage is at home.

</details>

## Contact

Shubho should understand the system fairly well (he coded the spectrometers and delay generator tabs), but if he's not sure and you have questions regarding the code (especially stage control) you can reach out to me.

**Ying Wan**\
Slack: Ying Wan\
Email: ywan4@ualberta.ca
