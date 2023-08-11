from flask import Flask
import flask.cli
import logging

def uptimecheck():

     logging.getLogger("werkzeug").disabled = True
     logging.getLogger("geventwebsocket.handler").disabled = True
     flask.cli.show_server_banner = lambda *args: None
     app = Flask(__name__)
     
     @app.route('/check')
     def re():
         return 'is Online!'
     
     app.run(debug=True, host='0.0.0.0', port=4567)
     
uptimecheck()