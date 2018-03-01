"""
Here we have all the lambda definitions and Gateway calls


@author: Eduard Cespedes Borràs
@mail: eduard@iot-partners.com
"""

from chalice import Chalice, NotFoundError, Response, BadRequestError
import json
import os
import boto3
import logging
from chalicelib.server import Server

app = Chalice(app_name='platform')

app.log.setLevel(logging.DEBUG)
app.debug = True

DEVICE_DATA_TABLE = os.getenv('APP_TABLE_NAME', 'defaultTable')
DEVICE_TABLE = os.getenv('DEVICES_TABLE_NAME', 'defaultTable')
SNS_TOPIC = os.getenv('SNS_TOPIC', 'defaultSNS')

device_data_table = boto3.resource('dynamodb').Table(DEVICE_DATA_TABLE)
device_table = boto3.resource('dynamodb').Table(DEVICE_TABLE)

sns_client = boto3.client('sns')

server = Server(device_data_table, device_table, sns_client, app.log)


@app.lambda_function()
def realtime_lambda_function(event, context):
    app.log.debug("This is the new call from the Lambda realtime")

    for record in event["Records"]:
        message = record["Sns"]["Message"]
        message_dic = json.loads(message)
        print("This is the SNS message! " + message_dic["DevEUI"])
        server.persist_data(message_dic)
        server.publish_data_payload_parser(message_dic)

    app.log.debug("realtime lambda done")
    return "worked"


@app.lambda_function()
def realtime_parsing_payload(event, context):
    app.log.debug("Parsing payload")

    for record in event["Records"]:
        message = record["Sns"]["Message"]
        message_dic = json.loads(message)
        parsed = Server.parse_payload(message_dic)
        virtual_tx = message["virtual_tx"]
        server.dispatch_alarm(virtual_tx, parsed)
        server.update_data(parsed)

    app.log.debug("Parsing payload done")
    return "worked"


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
        parsed_json = Server.parse_lora_json(request.json_body["body"])
        app.log.debug("Received event virtual_tx:" + parsed_json["virtual_tx"])
        server.publish_data_store_device(parsed_json)
        return parsed_json
    except KeyError:
            app.log.error("Error parsing LORA document")
            raise BadRequestError("Error parsing LORA document")


@app.route('/sigfox')
def sigfox():
    try:
        parsed_dic = Server.parse_sigfox_dic(app.current_request.to_dict())
        app.log.debug("Received event virtual_tx:" + parsed_dic["virtual_tx"])
        server.publish_data_store_device(parsed_dic)
        return Response(body='',
                        status_code=200,
                        headers={'Content-Type': 'text/plain'})
    except KeyError:
        app.log.error("Error parsing SIGFOX document")
        raise BadRequestError("Error parsing SIGFOX document")
