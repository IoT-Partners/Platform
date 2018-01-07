"""
All the logic that can and should be tested will be here


@author: Eduard Cespedes Borràs
@mail: eduard@iot-partners.com
"""

from chalice import Chalice, NotFoundError, Response
import json
from datetime import datetime
import boto3
import logging


class Server:
    def __init__(self, table, sns_client, log):
        self.table = table
        self.sns_client = sns_client
        self.log = log

    def publish_data(self):
        self.log.debug("This called from publish_data")
        self.sns_client.publish(
            TopicArn="arn:aws:sns:eu-west-1:488643450383:defaultSNS",
            Subject="Test from Lambda",
            Message="Good news everyone!"
        )
        return {"Published Event": "defaultSNS"}

    def persist_data(self, event=None, context=None):
        title = "The Big New Movie"
        year = 2015
        try:
            self.table.put_item(
                Item={
                    'title': title,
                    'year': year,
                    'info': {
                        'plot': "Nothing happens at all.",
                        'rating': "0"
                    }
                }
            )
        except Exception as e:
            raise NotFoundError("Error adding an element on dynamodb")
        self.log.debug("print: Data persisted")

    @staticmethod
    def parse_lora_json(json_body):
        jsonbody = json.loads(json_body)
        time = jsonbody["DevEUI_uplink"]["Time"]
        payload = jsonbody["DevEUI_uplink"]["payload_hex"]
        device_id = jsonbody["DevEUI_uplink"]["DevAddr"]

        return {"time": time, "payload": payload, "device_id": device_id, "type": "LORA", "extra": jsonbody}

    @staticmethod
    def parse_sigfox_dic(sigfox_dic):
        time = sigfox_dic["query_params"]["time"]
        d = datetime.utcfromtimestamp(int(time) / 1e3)
        json_date = str(d.isoformat()) + "Z"
        payload = sigfox_dic["query_params"]["data"]
        device_id = sigfox_dic["query_params"]["id"]

        return {"time": json_date, "payload": payload, "device_id": device_id, "type": "SIGFOX"}
