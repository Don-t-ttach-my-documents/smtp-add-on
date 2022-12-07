from parsing import parseMIMEFiles, isMimeMessage, formatBodyWithoutHeader, deformatHeaders, getMIMEFromstring
from flask import Flask, request, make_response

app = Flask(__name__)
PORT = 3201
HOST = "0.0.0.0"

@app.route("/upload", methods=["POST"])
def upload():
    message = request.get_data().decode("utf-8")
    messageMIME = getMIMEFromstring(message)
    if(not isMimeMessage(messageMIME)):
        #Voir exemple postfix_message_raw.txt
        if("This is a multi-part message in MIME format." in message):
            #TODO
            #Envoyer l'expéditeur à partir du filtre pour le recevoir ici
            message = parseMIMEFiles(formatBodyWithoutHeader(message, "test@imt.fr"))
            res = deformatHeaders(message)
        else:
            #Si le message n'est pas au format MIME, renvoyer le contenu
            res = message
    else:
        res = parseMIMEFiles(message)
    print(res)
    return make_response(res, 200)

if __name__ == "__main__":
    app.run(host=HOST, port=PORT)
