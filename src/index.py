
from parsing import smtpToJson, jsonToSmtp


from flask import Flask, request, make_response


app = Flask(__name__)
PORT = 3201
HOST = "0.0.0.0"


@app.route("/upload", methods=["POST"])
def upload():

    #print(type(request.get_data()))
    #print(request.get_data().decode("utf-8"))

    return make_response(jsonToSmtp(smtpToJson(request.get_data().decode("utf-8"))), 200)

if __name__ == "__main__":
    app.run(host=HOST, port=PORT)
