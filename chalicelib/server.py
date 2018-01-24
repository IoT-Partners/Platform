"""
All the logic that can and should be tested will be here


@author: Eduard Cespedes Borràs
@mail: eduard@iot-partners.com
"""

from chalice import Chalice, NotFoundError, Response
import json
from datetime import datetime
import hashlib
import dateutil
import boto3
import logging


def extract_lat_long(payload):
    lat_hex = payload[2:8]
    lat_str = int(lat_hex, 16)
    lat = (lat_str * 180 / 16777215) - 90
    lng_hex = payload[8:14]
    lng_str = int(lng_hex, 16)
    lng = (lng_str * 360 / 16777215) - 180
    geoloc = {"lat": str(lat), "lng": str(lng)}
    return geoloc


class Server:
    def __init__(self, table, sns_client, log):
        self.table = table
        self.sns_client = sns_client
        self.log = log

    def publish_data_store_device(self, data_to_publish):
        self.log.debug("publishing virtual_tx:" + data_to_publish["virtual_tx"])
        expected_message = json.dumps(data_to_publish)

        self.sns_client.publish(
            TopicArn="arn:aws:sns:eu-west-1:488643450383:StoreDeviceData",
            Subject="New IOT Event",
            Message=expected_message
        )

    def persist_data(self, event):
        try:
            self.table.put_item(Item=event)
        except Exception as e:
            print(e)
            raise NotFoundError("Error adding an element on dynamodb")
        self.log.debug("print: Data persisted")

    def update_data(self, event):
        try:
            if event is None:
                return

            update_expression = ''
            expression_attribute_values = {}
            if "GEO" in event:
                update_expression = 'SET geo = :val'
                expression_attribute_values = {
                    ':val': event["GEO"]
                }

            self.table.update_item(
                Key={"timeStamp": event["timeStamp"]},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values)

        except Exception as e:
            print(e)
            raise NotFoundError("Error updating an element on dynamodb")
        self.log.debug("print: Data persisted")

    @staticmethod
    def parse_payload(body):
        try:
            payload = body["payload"]
            str_packet_id = payload[:2]

            if str_packet_id == "10":
                return {"timeStamp": body["timeStamp"], "GEO": extract_lat_long(payload)}
            elif str_packet_id == "NEW_TYPE":
                return {"timeStamp": body["timeStamp"], "TMP": "32"}

        except Exception as e:
            print(e)

        return None

    @staticmethod
    def parse_lora_json(json_body):
        jsonbody = json.loads(json_body)
        time = jsonbody["DevEUI_uplink"]["Time"]
        payload = jsonbody["DevEUI_uplink"]["payload_hex"]
        device_id = jsonbody["DevEUI_uplink"]["DevAddr"]

        virtual_tx = device_id + "-" + time
        hash_object = hashlib.sha256(virtual_tx.encode())
        hex_dig = hash_object.hexdigest()

        dt = dateutil.parser.parse(time)
        strftime = dt.strftime("%s")
        time_millis = int(strftime) * 1000

        return {"virtual_tx": hex_dig, "time_json": time, "timeStamp": time_millis, "payload": payload,
                "DevEUI": device_id, "type": "LORA", "extra": json.dumps(jsonbody)}

    @staticmethod
    def parse_sigfox_dic(sigfox_dic):
        time = sigfox_dic["query_params"]["time"]
        d = datetime.utcfromtimestamp(int(time) / 1e3)
        json_date = str(d.isoformat()) + "Z"
        payload = sigfox_dic["query_params"]["data"]
        device_id = sigfox_dic["query_params"]["id"]

        virtual_tx = device_id + "-" + json_date
        hash_object = hashlib.sha256(virtual_tx.encode())
        hex_dig = hash_object.hexdigest()

        return {"virtual_tx": hex_dig, "timeStamp": int(time), "time_json": json_date, "payload": payload,
                "DevEUI": device_id, "type": "SIGFOX"}
