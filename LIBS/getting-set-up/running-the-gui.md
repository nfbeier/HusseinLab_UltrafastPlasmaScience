# Running/Closing the GUI

### Running

Once the code is installed and the Pi is serially connected and has been running uart\_receiver.py (if using the stage version), then you can change directories into the desired folder and run the GUI.

```bash
# Replace "LIBS_withStage" with "LIBS" to run the non-stage version instead
cd ./HusseinLab_UltrafastPlasmaScience/LIBS_withStage
python3 LIBS_GUI.py
```

Alternatively, you can run the code through an IDE like Anaconda.

### Closing

{% hint style="danger" %}
**Click "Disconnect All" before closing! If you forget to do so, reset the terminal/kernel.**&#x20;
{% endhint %}

I tried connecting the disconnect button to the close button, but that didn't work. I also tried disconnecting on closing, but that also didn't work. So it's just an annoying feature that I couldn't figure out.

Note: A graceful kill is important as the stage location is saved on closing. If something should occur on closing and the location is not saved properly,[ re-calibrate the stage](../hardware-overview/stage.md).
