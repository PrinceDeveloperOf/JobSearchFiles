import imaplib
import email
from email.header import decode_header
import json
import spacy
import openai
import re
import requests
import logging
import sys

if __name__ == '__main__':
    #Setup Logging
    logging.basicCOnfig(filename='JobSearch.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    #Setup stuff for receiving emails
    imap_server = imaplib.IMAP5('outlook.office365.com')
    username = "aUsername"
    password = "aPassword"
    mailbox = "Inbox"
    imap_server.login(username, password)
    #I can choose to get unseen or get mail from a certain email address or before a certain date
    #Get all messages in the email server
    #Returns message ids
    status, data = imap_server.search(None, 'ALL')
    
    if status == 'OK':
        message_ids = data[0].split()
        #Check each message
        for message_id in message_ids:
            #Get the whole message
            status, message_data = imap_server.fetch(message_id,'(RFC822)' )
        
            if status == 'OK':
                #Checking the validity of the message
                subject = ""
                for responsePart in messageData: 
                    if isinstance(responsePart, tuple):
                        msg = email.message_from_bytes(responsePart[1])

                        #Get the subject
                        subject = decode_header(msg['Subject'])[0][0]

                        if isinstance(subject, bytes):
                            #Decode if it's encoded
                            subject = subject.decode()
                    else:
                        logging.debug("An RFC822 message has returned not as a tuple")

                #The email message should be in html format
                email_message = message_data[0][1]
                #Find the job that was applied for 
                jobIndex = email_message.find("View Job")

                if jobIndex == -1:
                    logging.debug("Found a non application email")
                    continue

                
                pattern = r"https://www\.linkedin\.com/comm/jobs/view/\d+/"

                #Use regex to find a string
                jobLink = re.search(pattern, email_message, jobIndex)

                if jobLink == None:
                    logging.warning("Could not find a link in " + subject)
                    continue
                
                #remove /comm from jobLink
                jobLink = jobLink.replace("/comm", "")

                #Get the content of the job link
                #try block to see if the header is valid
                try:
                    response = requests.get(jobLink)
                    response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    logger.degug("Invalid link: " + jobLink + " in email: " + subject)
                    continue

                if response.status_code != 200:
                    logger.debug("Link: " + jobLink + " from " + subject + " returns code: " + response.status_code)
                    continue

                content = response.text
                #In the content find a string that loooks like this <div class="show-more-less-html__markup                 
                divIndex = content.find("<script type=\"application/ld+json\">")
                if divIndex == -1:
                    logger.debug("Could not find the line with the job description in " + jobLink + " in the email " + subject)
                    continue
                
                startOfJobDescriptionString = divIndex.end
                endOfJobDescriptionString = content.find("</script>",divIndex.end)

                #This should be the string of the job description this should be json
                jobDescriptionString = content[startOfJobDescriptionString:endOfJobDescriptionString]
                #If using GPT i should make the prompt to the ai a question
            

                #TODO check if valid JSON
                try:
                    jsonObject = json.loads(jobDescriptionString)
                except json.JSONDecodeError:
                    logger.debug("Invalid json from: " + subject)

                gptRequest = "Here is a job application " + jobDescriptionString + "\n Use it to fill the following form, seperate different items by with a new line: \n"
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
                    max_tokens=gptRequest.__sizeof__
                )
                stringToLookFor = ["Salary:", "Requirements:", "Certifications:", "Time:", "Company;", "Location:"]                
                categoryLocations = {} 
                
                for category in stringToLookFor:
                    categoryLocations[category] = aiResponse["text"].find(category)
                
                categoryOrder = []  
                sortedCategoryPairs = sorted(categoryLocations.items(), key = lambda x: x[1])#Is going to be an array where the first element is the first category that's given in the response of the ai
                
                categoryStrings = {} 
                
                for i, categoryPair in enumerate(sortedCategoryPairs):

                    if i < len(sortedCategoryPairs) - 1:
                        categoryStrings[categoryPair[0]] = aiResponse[categoryPair[1]:sortedCategoryPairs[i + 1]]
                    else:
                        categoryStrings[categoryPair[0]] = aiResponse[categoryPair[1]:]
            else:
                logger.warning("Failed to get message")
    else:
        logger.critical("Bad Email Credentials")


    imap_server.logout()