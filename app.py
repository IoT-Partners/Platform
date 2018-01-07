"""
Here we have all the lambda definitions and Gateway calls


@author: Eduard Cespedes Borràs
@mail: eduard@iot-partners.com
"""

from chalice import Chalice, NotFoundError, Response
import json
import os
import boto3
import logging
from chalicelib.server import Server

app = Chalice(app_name='platform')

app.log.setLevel(logging.DEBUG)
app.debug = True

MOVIE_TABLE = os.getenv('APP_TABLE_NAME', 'defaultTable')
SNS_TOPIC = os.getenv('SNS_TOPIC', 'defaultSNS')

table = boto3.resource('dynamodb').Table(MOVIE_TABLE)
sns_client = boto3.client('sns')

server = Server(table, sns_client, app.log)


@app.lambda_function()
def realtime_lambda_function(event, context):
    # print("Received event: " + json.dumps(event, indent=2))
    app.log.debug("This call is from the Lambda")
    # app.log.debug("From SNS: " + event)
    server.persist_data(event, context)
    return "test"


@app.route('/lambda')
def insert_data_in_lambda():
    app.log.debug("insert_data_in_lambda")
    return server.publish_data()


@app.route('/')
def index():
    print("print: This call is from the API Gateway")
    return Response(body='hello world!',
                    status_code=200,
                    headers={'Content-Type': 'text/plain'})


@app.route('/lora', methods=['POST', 'PUT'])
def lora():
    try:
        request = app.current_request
        app.log.debug(request.json_body)
        parsed_json = server.parse_lora_json(request.json_body["body"])
        return parsed_json
    except KeyError:
            app.log.error("Error parsing the document")
            raise NotFoundError()
