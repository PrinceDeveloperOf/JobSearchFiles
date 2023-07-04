#This file is a python file for turning an emial into a xml file
import os

path = "PATH HERER"
dirList = os.listdir(path)
files = [f for f in dirList if os.path.isFile(path+'/'+f)]



for file in files:
    currentFileMap = {}
    atBody = False
    with open(file, "r") as openFile:
    
        #It seems that a lot of the lines in a file end with =
        for line in openFile.readlines:
            if atBody:
                currentFileMap["Body"] = currentFileMap["Body"] + line[:-1]
            elif line.startswith("From: "):
                currentFileMap["From"] = line[len("From: ") - 1:]
            elif line.startswith("Subject: "):
                currentFileMap["Subject"] = line[len("Subject: ") -1:]
            elif line.startswith("Date: "):
                currentFileMap["Date"] = line[len("Date: ") -1:]
            elif line == "Content-ID: text-body":
                currentFileMap["Body"] = ""

#Save in a CSV file