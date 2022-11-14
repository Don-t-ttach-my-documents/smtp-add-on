import re
import requests
import sys
import base64
from werkzeug.datastructures import FileStorage

URL_TO_SERVER = "http://localhost:3200/"

def findBoundary(message):
    lines = message.split("\n")
    boundaryRe = re.compile('.*boundary="(.*)"')

    for line in lines:
        
        if boundaryRe.match(line) != None:
            return boundaryRe.match(line).group(1)

def sendFileServer(fileInfo, sender):
    #Envoie l'information du fichier en encodage base 64.
    #Repasser en binaire ? Laisser en base 64 ?
    #Dépend de comment on récupère/traitre le fichier après coup
    data = base64.b64decode(fileInfo["content"])
    files = {"file":(fileInfo["filename"], data, fileInfo["type"])}
    try:
        link = requests.post(URL_TO_SERVER+"upload", data={"email":sender},files=files)
    except requests.exceptions.ConnectionError as e:
        print(e)
        fileInfo["content"] = "url: blabla"
        return
    if(link.status_code==200):
        fileInfo["type"]="application/txt"
        fileInfo["filename"]=fileInfo["filename"].split(".")[0]+"_link.txt"
        fileInfo["content"] = URL_TO_SERVER+link.json()[0]
    else:
        print(link.json())
        exit(-1)


def smtpToJson(message):
    resJson = {}
    resJson["boundary"] = findBoundary(message)
    resJson["subject"]= ""
    resJson["from"]=""
    resJson["to"]=""
    resJson["body"] = {}
    resJson["body"]["body"] = ""
    resJson["body"]["attachments"]= []

    part = message.split("--"+resJson["boundary"])

    subjectRe = re.compile("Subject: (.*)")
    fromRe = re.compile("From: (.*)")
    toRe = re.compile("To: (.*)")
    for line in part[0].split("\n"):
        if subjectRe.match(line) != None: resJson["subject"] = subjectRe.match(line).group(1)
        elif fromRe.match(line) != None: resJson["from"]= fromRe.match(line).group(1)
        elif toRe.match(line) !=None: resJson["to"]=toRe.match(line).group(1)
    
    typeMessageRe = re.compile('Content-Type: (.*);?')
    filenameRe = re.compile('.*filename="(.*)"')
    encodageRe = re.compile('Content-Transfer-Encoding: (.*)')

    for p in part[1:]:
        lines = p.split("\n")

        if "attachment" in p:
                filename = ""
                typeDoc = ""
                content = ""
                encodage = ""
                for line in lines:
                    if typeMessageRe.match(line)!=None:
                        typeDoc = typeMessageRe.match(line).group(1)
                    elif filenameRe.match(line) !=None:
                        filename = filenameRe.match(line).group(1)
                    elif encodageRe.match(line)!=None:
                        encodage = encodageRe.match(line).group(1)
                    elif "MIME-Version:" in line:
                        pass
                    else:
                        content += line
            
                fileInfo = {"filename": filename, "type":typeDoc, "encodage":encodage, "content":content}
                #sendFileServer(fileInfo, resJson["from"])
                resJson["body"]["attachments"].append(fileInfo)
                
            
        elif "text" in p:
            filename = ""
            typeDoc = ""
            content = ""
            encodage = ""
            for line in lines:
                if typeMessageRe.match(line)!=None:
                    typeDoc = typeMessageRe.match(line).group(1)
                elif filenameRe.match(line) !=None:
                    filename = filenameRe.match(line).group(1)
                elif encodageRe.match(line)!=None:
                    encodage = encodageRe.match(line).group(1)
                elif "MIME-Version:" in line:
                    pass
                elif len(line)!=0:
                    content += "\n"+line
            
            fileInfo = {"type":typeDoc, "encodage":encodage, "content":content}
            resJson["body"]["body"] = fileInfo



    return resJson

def parseSMTPSession(session):
    message  = session.split("End message with period")[1].split("\n.\n")[0]
    return smtpToJson(message)

def jsonToSmtp(json):
    msg = "Content-Type: multipart/mixed; boundary=\""+json["boundary"]+"\"\nMIME-Version: 1.0\n"
    msg += "Subject: "+json["subject"]
    msg += "\nFrom: "+json["from"]+"\nTo: "+json["to"]
    msg += "\n\n--"+json["boundary"]

    msg +="\nContent-Type: "+json["body"]["body"]["type"]
    msg +="\nMIME-Version: 1.0\nContent-Transfer-Encoding: "+json["body"]["body"]["encodage"]
    msg += "\n"+json["body"]["body"]["content"]
    
    for attach in json["body"]["attachments"]:
        msg += "\n--"+json["boundary"]
        msg += "\nContent-Type: "+ attach["type"]
        msg += "\nMIME-Version: 1.0\nContent-Transfer-Encoding: "+attach["encodage"]
        msg += "\nContent-Disposition: attachment; filename=\""+attach["filename"]+"\""
        msg += "\n\n"+attach["content"]

    msg += "\n\n--"+json["boundary"]+"--\n.\n"
    return msg

##TODO
#Reconstruire le mail
##

if __name__=="__main__":
    if len(sys.argv)!=2: exit(0)
    with open(sys.argv[1], 'r') as file:
        msg = file.read()
        file.close()
        resJson = parseSMTPSession(msg)
        #print(resJson)
        for fileInfo in resJson["body"]["attachments"]:
            sendFileServer(fileInfo, resJson["from"])
        print(jsonToSmtp(resJson))

