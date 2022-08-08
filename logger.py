import serial
import adafruit_fingerprint
import time
import pymongo
import os
import threading
import datetime

# If using with Linux/Raspberry Pi and hardware UART:
uart = serial.Serial("/dev/ttyUSB0", baudrate=57600, timeout=1)
# Can also be
# uart = serial.Serial("/dev/ttyS0", baudrate=57600, timeout=1)

# If using with Linux/Raspberry Pi 3 with pi3-disable-bte
# uart = serial.Serial("/dev/ttyAMA0", baudrate=57600, timeout=1)

finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

client = pymongo.MongoClient("MONGODB URI")
db = client["atLab"]
collection = db["nameList"]

def sendAndCompare(sensor : adafruit_fingerprint.Adafruit_Fingerprint, a, b):
    """Sends the raw data in slots 1 and 2, compares then and returns a boolean\n
        Example parameter: \n
        list(data) if data is from file saved by enroll_save_to_file\n
        bytearray(data) if data is from get_fpdata"""
    sensor.send_fpdata(a, "char", 1)
    sensor.send_fpdata(b, "char", 2)

    res = finger.compare_templates()
    if res == adafruit_fingerprint.OK:
        return True
    if res == adafruit_fingerprint.NOMATCH:
        # print("Templates do not match!")
        pass
    else:
        print("Other error!")
    return False

def template(sensor : adafruit_fingerprint.Adafruit_Fingerprint, slot : int):
    """Templates the fingerprint and store it in the desired slot\n
    Returns True if successfully templated, else print the error and return False"""
    print("Templating...", end="", flush=True)
    i = sensor.image_2_tz(slot)
    if i == adafruit_fingerprint.OK:
        print("Templated")
        return True
    else:
        if i == adafruit_fingerprint.IMAGEMESS:
            print("Image too messy")
        elif i == adafruit_fingerprint.FEATUREFAIL:
            print("Could not identify features")
        elif i == adafruit_fingerprint.INVALIDIMAGE:
            print("Image invalid")
        else:
            print("Other error")
        return False

def compareFolder(sensor : adafruit_fingerprint.Adafruit_Fingerprint, path : str):
    """iterate through the directory and compare every fingerprint\n
        returns the matching file's name if found any, else return None\n
        NOTE: A fingerprint must be templated in slot 1 before this function executes"""
    for filename in os.listdir(path):
        f = os.path.join(path, filename)
        # checking if it is a .dat file
        if filename.endswith(".dat"):
            with open(f, "rb") as file:
                data = file.read()
            finger.send_fpdata(list(data), "char", 2)
            res = sensor.compare_templates()
            if res == adafruit_fingerprint.OK:
                return filename.split('.')[0]

def askForFinger(sensor : adafruit_fingerprint.Adafruit_Fingerprint):
    """Waits until a finger is detected, then ask the sensor to take the image and store it in memory"""
    print("Please put finger")
    while True:
        i = finger.get_image()
        if i == adafruit_fingerprint.OK:
            print("Image taken")
            break
        if i == adafruit_fingerprint.NOFINGER:
            # print(".", end="", flush=True)
            pass
        elif i == adafruit_fingerprint.IMAGEFAIL:
            print("Imaging error")
            return False
        else:
            print("Other error")
            return False

def enroll_save_to_file(sensor : adafruit_fingerprint.Adafruit_Fingerprint, path : str, name : str):
    """Take a 2 finger images and template it, then store it in a file"""
    for fingerimg in range(1, 3):
        if fingerimg == 1:
            print("Place finger on sensor...", end="", flush=True)
        else:
            print("Place same finger again...", end="", flush=True)

        while True:
            i = sensor.get_image()
            if i == adafruit_fingerprint.OK:
                print("Image taken")
                break
            if i == adafruit_fingerprint.NOFINGER:
                print(".", end="", flush=True)
            elif i == adafruit_fingerprint.IMAGEFAIL:
                print("Imaging error")
                return False
            else:
                print("Other error")
                return False

        print("Templating...", end="", flush=True)
        i = sensor.image_2_tz(fingerimg)
        if i == adafruit_fingerprint.OK:
            print("Templated")
        else:
            if i == adafruit_fingerprint.IMAGEMESS:
                print("Image too messy")
            elif i == adafruit_fingerprint.FEATUREFAIL:
                print("Could not identify features")
            elif i == adafruit_fingerprint.INVALIDIMAGE:
                print("Image invalid")
            else:
                print("Other error")
            return False

        if fingerimg == 1:
            print("Remove finger")
            while i != adafruit_fingerprint.NOFINGER:
                i = finger.get_image()

    print("Creating model...", end="", flush=True)
    i = sensor.create_model()
    if i == adafruit_fingerprint.OK:
        print("Created")
    else:
        if i == adafruit_fingerprint.ENROLLMISMATCH:
            print("Prints did not match")
        else:
            print("Other error")
        return False

    print("Downloading template...")
    data = sensor.get_fpdata("char", 1)
    fpath = path + "/" + name + ".dat"
    with open(fpath, "wb") as file:
        file.write(bytearray(data))
    print("Template is saved in " + fpath + " file.")

    return True

def askSecondThenSave(sensor : adafruit_fingerprint.Adafruit_Fingerprint, path : str, name : str):
    """Asks the second image for registering new user, creates a model then save it to a file
        Returns True if successful, False if error"""
    askForFinger(sensor)
    template(sensor, 2)

    print("Creating model...", end="", flush=True)
    i = sensor.create_model()
    if i == adafruit_fingerprint.OK:
        print("Created")
    else:
        if i == adafruit_fingerprint.ENROLLMISMATCH:
            print("Prints did not match")
        else:
            print("Other error")
        return False

    print("Downloading template...")
    data = sensor.get_fpdata("char", 1)
    fpath = path + "/" + name + ".dat"
    with open(fpath, "wb") as file:
        file.write(bytearray(data))
    print("Template is saved in " + fpath + " file.")

    return True

def resetAt4(collection):
    while True:
        time.sleep(0.1)#It doesnt need to go that fast
        today = datetime.datetime.now()
        hours = int(today.strftime("%H"))
        minutes = int(today.strftime("%M"))
        if(hours == 4 and minutes == 0):
            #Find all with signintime not = None
            for doc in collection.find({"signintime": {"$ne" : None}}):
                doc["signintime"] = None
                collection.replace_one({"_id" : doc["_id"]}, doc)
            time.sleep(65)#Waits for 65s in case errors

resetClock = threading.Thread(target=resetAt4, args=(collection,), name='resetClock')
resetClock.start()

while True:
    #Prevent someone from holding the sensor
    if finger.get_image() != adafruit_fingerprint.NOFINGER: 
        continue

    print("----------------")
    if finger.read_templates() != adafruit_fingerprint.OK:
        raise RuntimeError("Failed to read templates")
    # print("Fingerprint templates: ", finger.templates)
    if finger.count_templates() != adafruit_fingerprint.OK:
        raise RuntimeError("Failed to read templates")
    # print("Number of templates found: ", finger.template_count)
    if finger.set_sysparam(6, 2) != adafruit_fingerprint.OK:
        raise RuntimeError("Unable to set package size to 128!")
    if finger.read_sysparam() != adafruit_fingerprint.OK:
        raise RuntimeError("Failed to get system parameters")

    #Ask for finger, then compare all fingers in directory
    askForFinger(finger)
    template(finger, 1)
    res = compareFolder(finger, "data")
    if (not res):
        #if no response ask if they already registered, if not, take the second image, ask for their name, and store it in the folder
        uin = input("Have you already registered? [y/n]: ")
        if uin == 'n':
            #ask name
            name = input("Please enter your name: ")
            while '.' in name:
                name = input("Please enter your name, no \'.\' please: ")
            #take second image and save
            res = askSecondThenSave(finger, "data", name)
            if res:
                print("Successfully registered " + name + ", put your finger back on once again to sign in")
            else:
                print("Register unsuccessful, please try again")
    else:
        #sends request to db
        #sends int(time.time())
        doc = collection.find_one({"name" : res})
        if not doc: #if doesnt find shit
            newDoc = {
                "name": res,
                "signintime": None,
                "totalTime": 0,
                "totaltimeminutes": 0
            }
            collection.insert_one(newDoc)
        else: 
            if not doc["signintime"]:#If no login time, log them in
                doc["signintime"] = str(int(time.time()))
                print("Welcome", res)
            else:
                doc["totalTime"] += int(time.time()) - int(doc["signintime"])
                doc["totaltimeminutes"] = round(doc["totalTime"] / 60.0, 2)
                doc["signintime"] = None
                print("Bye", res)
            collection.replace_one({"_id" : doc["_id"]}, doc)
        
