---
description: Controls the manual and automatic translations of the stage.
---

# Translation Stage

![Translation Stage tab of LIBS GUI](<../.gitbook/assets/Translation Stage Tab>)

### Manual:&#x20;

* There was no need to move absolutely, so it only moves relatively.
* Up, down, left, and right step lengths can be changed using the "Manual Step Length" box (mesaured in mm).
* "Set Home" changes the "Relative Location" to 0,0 and all relative location messages will refer to its distance from home. It can also be considered as a reference point.
*  "Return Home" moves to home.

### Raster:

1. Manual move to and set the top left corner of the sample as home. All movements will be relative to this point.
2. Set sample height (mm) and width (mm).
   * "Sample Height" is the length of the sample along the y-axis. It can be inputted in the text box or calibrated (see point 3) by the "Set y Bound" button.
   * "Sample Width" is the length of the sample along the x-axis. Similarily, it can be inputted in the text box or calibrated (see point 3) by the "Set x Bound" button.
   * Calibrating/Setting Bounds:&#x20;
     * To set both bounds: move to the opposite corner of home (bottom right) using manual translations and hit both set bound buttons
     * To set one bound: move to another corner (right or bottom left) using manual translations and hit the corresponding button
3. Input "Step Length" (mm).
4. Number of "Max Shots" takable will be printed. Input your desired "Number of Shots".
5. **OPTION 1**: "Test Raster Path" will only go through the stage movements. The delay generator and spectrometers are not involved. Used for testing.\
   **OPTION 2**: "Single Shot" combines the delay generator, spectrometers, and stage to automate data collection. See [single-shot.md](single-shot.md "mention").
