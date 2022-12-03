import email
import sys
import base64
import requests

URL_TO_FILE_SERVER = "http://localhost:3200"

def sendFileServer(fileInfo, sender):

    data = base64.b64decode(fileInfo["content"])
    files = {"file":(fileInfo["filename"], data, fileInfo["type"])}
    try:
        link = requests.post(URL_TO_FILE_SERVER+"/upload", data={"email":sender.strip()},files=files)
    except requests.exceptions.ConnectionError as e:
        #####TO DEBUG#######
        #Supprimer ce code au déploiement
        print(e)
        fileInfo["filename"] = fileInfo["filename"].split(".")[0]+"_link.txt"
        fileInfo["content"] = base64.b64encode("url: failed to connect".encode('utf-8'))
        ###################
        return
    if(link.status_code==200):
        fileInfo["type"]="application/txt"
        fileInfo["filename"]=fileInfo["filename"].split(".")[0]+"_link.txt"
        fileInfo["content"] = str(base64.b64encode(((URL_TO_FILE_SERVER+link.json()[0])).encode('utf-8')).decode('utf-8')) + "\n"
    else:
        print(link.json())
        exit(-1)

def parseMIMEFiles(mimeMessage):
    mime = getMIMEFromstring(mimeMessage)
    if not isMimeMessage(mime): return mime.as_string()

    sender = mime.get('From', "failed@mail.com")
    parts = mime.get_payload()
    for part in parts:
        if None== part.get('Content-disposition') or "attachment" not in part.get('Content-disposition'):
            continue

        fileInfo = {}
        fileInfo["filename"] = part.get_filename()
        fileInfo["content"] = part.get_payload()
        fileInfo["type"] = part.get_content_type()

        sendFileServer(fileInfo, sender)
        part.replace_header('Content-disposition', "attachment; filename=\""+fileInfo["filename"]+'"')
        part.replace_header('Content-type', "text/plain; charset=UTF-8; name=\""+fileInfo["filename"]+'"')
        part.set_payload(fileInfo["content"])
    return mime.as_string()

def isMimeMessage(mimeMessage):
    return mimeMessage.is_multipart()

def getMIMEFromstring(message):
    return email.message_from_string(message)

def getBoundaryWithoutHeader(message):
    return message.split("\n")[1][2:]

#Voir exemple postfix_message_raw (exemple de ce qui est reçu par le filtre)
def formatBodyWithoutHeader(message, sender):
    boundary = getBoundaryWithoutHeader(message)
    newMessage = "Content-Type: multipart/mixed; boundary="+boundary+"\n"
    newMessage += "From: "+sender+"\n"+message
    return newMessage

#enleve les headers ajoutés pour le parsing du message
def deformatHeaders(message):
    return "\n".join(message.split("\n")[2:])

#Tester le parsing avec un fichier
if __name__=="__main__":
    if len(sys.argv)!=2:
        print("Please provide the path to the file to test in parameters")
        exit(0)
    with open(sys.argv[1], 'r') as file:
        msg = file.read()
        file.close()
    msg = formatBodyWithoutHeader(msg, "test2@mail.fr")
    print(deformatHeaders(parseMIMEFiles(msg)))

