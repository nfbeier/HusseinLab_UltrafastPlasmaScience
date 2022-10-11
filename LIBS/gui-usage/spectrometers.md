---
description: >-
  Takes in experimental parameters and plots the spectrometer spectrums for each
  shot.
---

# Spectrometers

![Spectrometers tab of LIBS GUI](<../.gitbook/assets/Spectrometers Tab>)

* The path of the directory can be typed into the text box or browsed for using the browse "button".&#x20;
* All parameters have to be filled before hitting "Set" or gui will crash.
* When "Single Shot" mode is being used, all of the spectrums and parameters will be saved as an hdf5 file in the specified directory.&#x20;
  * As long as the gui is open, the files will be saved with the date and number id starting at 1 and increasing by 1 each shot. When the gui is closed and reopened the number id will start at 1 again.

{% hint style="danger" %}
**If the gui is closed and reopened on the same day, the old files will be rewritten so write to a different directory**
{% endhint %}

{% hint style="danger" %}
**Once all lines of inputs is inputted, ensure you click "Set" or else the action will not compute!**
{% endhint %}
