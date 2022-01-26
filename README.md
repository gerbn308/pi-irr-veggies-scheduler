# pi-irr-veggies
Extremely simplistic irrigation scheduler for Raspberry Pi controlled setups using a temperature probe for a Raspberry Pi that is accessed via an API. My personal weather station on Ambient weather is also accessed because once upon a time this code was used to apply water to an outdoor garden that I abandoned due to rampant weed problems.

My garage was added because it was easiest to piggyback on this project for data storage and graphing.

My setup involves multiple components.

1. Greenhouse - Where the crops are grown, has a DHT22 Sensor - https://smile.amazon.com/gp/product/B0795F19W6/ accessible by API
2. Garage - Where my Valve is controlled, also has a temperature sensor so I can monitor the garage temperatures in the winter.
3. Pi Cluster - Where this Docker image runs.
4. Weather Station - My personal weather station that was utilized when I irrigated my garden. Now its used to avoid situations in the spring and fall when it would be cold enough to potentially freeze the hose.


INSTRUCTIONS:
1. Calibrate the irrigation rates in irrigation.py to be accurate for your setup.
2. Modify weather.py with station details or modify code to bypass if you don't wish to use this.

IRRIGATION CONFIG DEFINITIONS:

* MIN_IRRIGATION - Minimum amount of irrigation to apply at a given time in millimeters
* BASE_WEEKLY_WATER - Base Weekly Water need in millimeters
* BASE_TEMP - Base Temperature for the weekly need in Celsius
* BASE_TEMP_RANGE - Increments to use to add additional irrigation needs in Celsius. This VERY crudely simulates evaporation.
* BASE_TEMP_INCREASE - How much additional water to apply for the BASE_TEMP_RANGE increment. This value is in millimeters
* IRRIGATION_SPINUP_SECONDS - How long in seconds it takes for your irrigation system to achieve full water pressure. I recommend timing how long it takes to start up. I used an SSH client on my phone to trigger the spinup so that I could time it.
* CUPS_PER_5MIN - How many cups of water were collected in a 5 minute period from a single hole in the PVC to calibrate the application rate.

CALIBRATION:
To calibrate my system I used a measuring cup at the fatherst point in the irrigation piping system. I manually triggered the irrigation to run and collected water for 5 minutes. 

IMPORTANT NOTICES:

1. This does not confirm that water was actually applied. If your water isn't running or the valve can't open this will not know. Adding some sort of flow sensor could help with this but it hasn't been an issue unless my Solenoid valve falls on its side.
2. If the Pi crashes out for whatever reason during application, the valve will remain open with water being applied until you can reset it.
3. This is not designed to confirm to any laws that may exist so check your local, state, and national regulations before utilizing this. If you are found to be in violation I am in no way responsible.

DOCUMENTATION:

Default Values Taken Roughly from https://bonnieplants.com/library/how-much-water-do-vegetables-need/

Calibration Help: http://www.sprinklerwarehouse.com/DIY-Calculating-Precipitation-Rate-s/7942.htm

Hardware Build Design that I used: http://www.instructables.com/id/Raspberry-Pi-Irrigation-Controller/?ALLSTEPS

PVC Pipe design if building outdoors: https://digitalcommons.usu.edu/cgi/viewcontent.cgi?referer=https://www.google.com/&httpsredir=1&article=2054&context=extension_curall
	If you space your PVC holes more than 3 inches apart, you'll want to modify the squareFeetPerHole in irrigation.py to ensure proper calibration.