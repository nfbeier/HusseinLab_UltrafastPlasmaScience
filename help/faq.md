---
description: Issues that gave me a headache
---

# 🤔 FAQ

## Motor Issues

<details>

<summary>Why is the motor "jammed" (it makes a noise but nothing moves)?</summary>

Unplug the entire system and then ensure the motors are securely plugged into the motor drivers. Sometimes if the connection is loose, it will bug out.

</details>

<details>

<summary>Why aren't the motors rotating?</summary>

1. Make sure the system is plugged in.
2. The Pi takes a few minutes to boot up, try again in a few minutes.
3. Check that messages are being serially communicated. You can do this by VNCing or SSHing onto the Pi (see [configuring-your-raspberry-pi.md](../getting-set-up/configuring-your-raspberry-pi.md "mention"))

</details>

<details>

<summary>Why does only one motor rotate and the other doesn't?</summary>

1. Check that both motors are plugged in
2. Unplug the whole system and then unplug and replug the motors.

</details>

## Serial Issues

<details>

<summary>Error Message: Don't have permission to read COM11 (or whatever port the Pi is connected through)</summary>

Try unplugging and plugging back in the USB. For whatever reason, this error randomly pops up at times.

</details>
