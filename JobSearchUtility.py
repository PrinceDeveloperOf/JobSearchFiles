import imaplib
import openai
import re
import requests
if __name__ == '__main__':
    #Setup stuff for receiving emails
    imap_server = imaplib.IMAP5('outlook.office365.com')
    username = "aUsername"
    password = "aPassword"
    imap_server.login(username, password)
    mailbox = "Inbox"
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
            #TODO check if message was successful 
            if status == 'OK':
                #The email message should be in html format
                email_message = message_data[0][1]
                #Find the job that was applied for 
                jobIndex = email_message.find("View Job")
                
                pattern = r"https://www\.linkedin\.com/comm/jobs/view/\d+/"
                #Use regex to find a string
                jobLink = re.search(pattern, email_message, index)

                #remove /comm from jobLink

                #Get the content of the job link
                response = requests.get(jobLink)
                content = response.text
                #In the content find a string that loooks like this <div class="show-more-less-html__markup                 
                divIndex = content.find("<script type=\"application/ld+json\">")
                startOfJobDescriptionString = divIndex.end
                endOfJobDescriptionString = content.find("</script>",divIndex.end)

                #This should be the string of the job description this should be json
                jobDescriptionString = content[startOfJobDescriptionString:endOfJobDescriptionString]
                #If using GPT i should make the prompt to the ai a question
            

                #TODO check if valid JSON

                #Send it to GPT  
                openai.api_key = 'apikey'

                aiResponse = openai.Completion.create(
                    engine='text-davinci-003', #What engine should i choose?
                    prompt=jobDescriptionString,
                    max_tokens=100
                )



    imap_server.logout()