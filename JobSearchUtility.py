import email
from email.header import decode_header
from datetime import datetime
import json
import openai
import re
import requests
import logging
import sys
import csv
import imaplib

def parseEmail(subject, emailMessage,stringsToLookFor, categoriesForData, csvData, newData):
    #Find the job that was applied for 
    #Could probably search for a growing list of things that 
    jobIndex = emailMessage.find("View job")
    

    if jobIndex == -1:
        logging.debug("Found a non application email")
        return -1

    
    pattern = r"https://www\.linkedin\.com/comm/jobs/view/\d+/"

    #Use regex to find a string
    jobLinkIndex = re.search(pattern, emailMessage)

    if jobLinkIndex == None:
        logging.warning("Could not find a link in " + subject)
        return -1
    
    #remove /comm from jobLinkIndex
    #jobLink = jobLinkIndex.sub("/comm", "")
    #Theres only one match so get the first group is the whole match
    jobLink = jobLinkIndex.group(0)
    jobLink = jobLink.replace("/comm","")

    #Get the content of the job link
    #try block to see if the header is valid
    try:
        response = requests.get(jobLink)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.degug("Invalid link: " + jobLink + " in email: " + subject)
        return -1

    if response.status_code != 200:
        logger.debug("Link: " + jobLink + " from " + subject + " returns code: " + response.status_code)
        return -1

    content = response.text
    #In the content find a string that loooks like this <div class="show-more-less-html__markup                 
    divIndex = content.find("<script type=\"application/ld+json\">")
    if divIndex == -1:
        logger.debug("Could not find the line with the job description in " + jobLink + " in the email " + subject)
        return -1
    
    startOfJobDescriptionString = divIndex.end
    endOfJobDescriptionString = content.find("</script>",divIndex.end)

    #This should be the string of the job description this should be json
    jobDescriptionString = content[startOfJobDescriptionString:endOfJobDescriptionString]
    #If using GPT i should make the prompt to the ai a question


    #Checks if it's JSON
    try:
        jsonObject = json.loads(jobDescriptionString)
    except json.JSONDecodeError:
        logger.debug("Invalid json from: " + subject)

    gptRequest = "Here is a job application " + jobDescriptionString + "\n Use it to fill the following form, seperate different items with a new line: \n"
    + "Salary: <Enter salary here>\n"
    + "Requirements: <Enter requirements here>\n"
    + "Certifications: <Enter certifications needed here>\n"
    + "Time: <Enter time of shift here>\n" 
    + "Company: <Enter name of company here>\n"
    + "Location: <Enter location of job here>\n"

    #Send it to GPT  
    openai.api_key = 'apikey'

    aiResponse = openai.Completion.create(
        engine='text-davinci-003', #What engine should i choose?
        prompt=jobDescriptionString,
        max_tokens=len(gptRequest)
    )

    categoryLocations = {} 
    
    for category in stringToLookFor:
        categoryLocations[category] = aiResponse["text"].find(category)
        if categoryLocations[category] == -1:
            logger.warning("Category: " + category + " was not found in message: " + subject)    
            del(categoryLocations[category])
    sortedCategoryPairs = sorted(categoryLocations.items(), key = lambda x: x[1])#Is going to be an array where the first element is the first category that's given in the response of the ai
    
    categoryStrings = {} 
    
    for i, categoryPair in enumerate(sortedCategoryPairs):

        if i < len(sortedCategoryPairs) - 1:
            categoryStrings[categoryPair[0]] = aiResponse[categoryPair[1]:sortedCategoryPairs[i + 1][1]]
        else:
            categoryStrings[categoryPair[0]] = aiResponse[categoryPair[1]:]
    
    newData[0] = categoryStrings[categoriesForData[0]]
    newData[1] = categoryStrings[categoriesForData[1]]
    newData[2] = categoryStrings[categoriesForData[2]]
    newData[3] = categoryStrings[categoriesForData[3]]
    newData[4] = categoryStrings[categoriesForData[4]]
    newData[5] = categoryStrings[categoriesForData[5]]
    newData[6] = subject
    newData[7] = jobDescriptionString
        

    csvData.append(newData)
        
    #Process the entries for the categoryStrings
    
    #processedCategories = {}
    #for categoryString in categoryStrings:
    #    stringToParse = categoryString[1]
    #    processedCategories[categoryString[0]] = stringToParse.split()

    return 1

if __name__ == '__main__':
    #Setup Logging
    logging.basicConfig(filename='JobSearch.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    useEmail = False
    if useEmail:
        #Setup stuff for receiving emails
        imap_server = imaplib.IMAP4('outlook.office365.com')
        username = "aUsername"
        password = "aPassword"
        mailbox = "Inbox"
        imap_server.login(username, password)
        
        #I can choose to get unseen or get mail from a certain email address or before a certain date
        #Get all messages in the email server
        #Returns message ids
        sinceDate = datetime.datetime(2023, 6, 1).strftime("%d-%b-%y")
        status, data = imap_server.search(None, f'(SINCE "{sinceDate}")')

        if status == 'OK':
            message_ids = data[0].split()
            #Check each message
            stringToLookFor = ["Salary:", "Requirements:", "Certifications:", "Time:", "Company;", "Location:"]                
            categoriesForData = stringToLookFor  
            categoriesForData.append("subject")
            categoriesForData.append("message")

            csvData = [categoriesForData]
            newData = [None] * len(categoriesForData)
            
            
            for message_id in message_ids:
                #TODO if the message already exits then continue
                #Get the whole message
                status, messageData = imap_server.fetch(message_id,'(RFC822)' )
            
                if status == 'OK':
                    #Checking the validity of the message
                    subject = ""
                    for responsePart in messageData: 
                        if isinstance(responsePart, tuple):
                            msg = email.message_from_bytes(responsePart[1])

                            #Get the subject
                            subject = decode_header(msg['Subject'])[0][0]

                            #Is this is intance needed?
                            if isinstance(subject, bytes):
                                #Decode if it's encoded
                                subject = subject.decode()
                        else:
                            logging.debug("An RFC822 message has returned not as a tuple")

                    #The email message should be in html format
                    email_message = messageData[0][1]

                    if parseEmail(subject, email_message, stringToLookFor,categoriesForData, csvData,newData  ):
                        logger.debug("Succefully parsed an email")
                    else:
                        logger.degug("Parsing an email didn't work")
                    
                    #Process the entries for the categoryStrings
                    
                    #processedCategories = {}
                    #for categoryString in categoryStrings:
                    #    stringToParse = categoryString[1]
                    #    processedCategories[categoryString[0]] = stringToParse.split()
                else:
                    logger.warning("Failed to get message")
            
            with open("csvData" + datetime.now(), mode='w', newline='') as file:
                writer = csv.writer(file)
                
                for row in csvData:
                    writer.writerow(row)
                    
        else:
            logger.critical("Bad Email Credentials")


        imap_server.logout()
    else:
        logger.debug("Did not attempt to use email") 


    #open csv file with email data
    with open('email.csv', 'r', newline='') as csvFile:
        emailCSV = csv.reader(csvFile)
        headers = next(emailCSV)
        for email in emailCSV:
            
            
            stringtolookfor = ["salary:", "requirements:", "certifications:", "time:", "company;", "location:"]                
            categoriesfordata = stringtolookfor  
            categoriesfordata.append("subject")
            categoriesfordata.append("message")

            csvdata = [categoriesfordata]
            newData = [None] * len(categoriesfordata)
            
            print(email[3])
            parseEmail(email[1],email[3],stringtolookfor,categoriesfordata,csvdata, newData)
            
            print(newData);
           
            
 
    #With every row of data 
    
    #Parse it
    
    #Take the response which for now will be a response from gpt and put it into a file
    
    #That file should be the inteded result
