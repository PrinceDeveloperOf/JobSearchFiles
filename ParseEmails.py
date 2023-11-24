#This file is a python file for turning an emial into a xml file
import os
import csv
import logging
import hashlib
import datetime
path = "PATH HERE"
dirList = os.listdir(path)
files = [f for f in dirList if os.path.isfile(path+'/'+f)]

fileMaps = []
logging.basicConfig(filename='Email' + datetime.datetime.now().time().strftime("%H-%M-%S") + ".log", level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


for file in files:
    currentFileMap = {}
    atBody = False
    with open(path+'\\'+file, "r") as openFile:
    
        #It seems that a lot of the lines in a file end with =
        for line in openFile:
            if atBody:
                currentFileMap["Body"] = currentFileMap["Body"] + line[:-1]
            elif line.startswith("From: "):
                logger.debug('found a sender')
                currentFileMap["From"] = line[len("From: ") - 1:]
            elif line.startswith("Subject: "):
                logger.debug('found a subject')
                currentFileMap["Subject"] = line[len("Subject: ") -1:]
            elif line.startswith("Date: "):
                logger.debug('found a date')
                currentFileMap["Date"] = line[len("Date: ") -1:]
            elif line.startswith("Content-ID: text-body"):
                logger.debug('found a body')
                currentFileMap["Body"] = ""
                atBody = True
            #else:
            #    logger.warning("Nothing found")
    if "Body" in currentFileMap:# and "From" in currentFileMap: #and "Subject" in currentFileMap and "Date" in currentFileMap and "Body" in currentFileMap:
        logger.debug("Appending a file")
        fileMaps.append(currentFileMap)
        

#Save in a CSV file
with open(str(datetime.datetime.now()), 'w', newline='') as csvFile:
#Version with hashed name
#with open(hashlib.sha256(str(datetime.datetime.now()).encode()).hexdigest(), 'w', newline='') as csvFile:
    writer = csv.writer(csvFile)
    writer.writerow(["From", "Subject", "Date", "Body"])
    for file in fileMaps:
        writer.writerow([file["From"], file["Subject"], file["Date"], file["Body"]])
        
