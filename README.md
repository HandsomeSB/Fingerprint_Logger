# Fingerprint_Logger


### Overview
Fingerprint sensor to record lab time for members. 
For new member register, 2 fingerprints of the same finger must be sampled. It will ask for name and save the encoded fingerprint information in a file. 
Signin time and lab hours will be recorded in a MongoDB cluster. 

### Requirements
At least one USB port, 3 recommended to setup.

A computer/single board computer, raspberry pi recommended but others work as well. This project has been experimented with TinkerBoard

Python(This project uses python version 3.5.3)

Adafruit Blinka
https://pypi.org/project/Adafruit-Blinka/

pymongo
https://pypi.org/project/pymongo/

pyserial
https://pypi.org/project/pyserial/

Adafruit_fingerprint.py
https://github.com/adafruit/Adafruit_CircuitPython_Fingerprint/blob/main/adafruit_fingerprint.py
