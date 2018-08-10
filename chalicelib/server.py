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


def extract_keep_alive(payload):
    interval = payload[2:4]
    interval_int = int(interval, 16)
    voltatge_hex = payload[4:8]
    voltatge_hex_dec = int(voltatge_hex, 16) / 1000
    return {"interval": str(interval_int), "voltage": str(voltatge_hex_dec)}


class Server:
    def __init__(self, device_data_table, device_table, sns_client, log):
        self.table = device_data_table
        self.sns_client = sns_client
        self.log = log

    # StoreDeviceData executes realtime_lambda_function
    def publish_data_store_device(self, data_to_publish):
        self.log.debug("publishing virtual_tx:" + data_to_publish["virtual_tx"])
        expected_message = json.dumps(data_to_publish)

        self.sns_client.publish(
            TopicArn="arn:aws:sns:eu-west-1:488643450383:StoreDeviceData",
            Subject="New IOT Event",
            Message=expected_message
        )

    # PayloadParser executes realtime_parsing_payload
    def publish_data_payload_parser(self, data_to_publish):
        self.log.debug("publishing virtual_tx for payload" + data_to_publish["virtual_tx"])
        expected_message = json.dumps(data_to_publish)

        self.sns_client.publish(
            TopicArn="arn:aws:sns:eu-west-1:488643450383:PayloadParser",
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
            if "KA" in event:
                update_expression = 'SET ka = :val'
                expression_attribute_values = {
                    ':val': event["KA"]
                }

            response = self.table.update_item(
                Key={"timeStamp": event["timeStamp"], "DevEUI": event["DevEUI"]},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues="UPDATED_NEW"
            )

            self.log.debug("print: Data persisted")
            return response

        except Exception as e:
            print(e)
            raise NotFoundError("Error updating an element on dynamodb")

    # NotifySNS sends a mail
    def dispatch_alarm(self, virtual_tx, data):
        is_alarm_activated = False

        if "KA" in data:
            voltage = float(data["KA"]["voltage"])
            if voltage <= 2.65:
                is_alarm_activated = True

        if not is_alarm_activated:
            return

        data.update({"virtual_tx": virtual_tx})
        expected_message = json.dumps(data)
        self.log.debug("dispatch_alarm virtual_tx:" + virtual_tx)
        self.sns_client.publish(
            TopicArn="arn:aws:sns:eu-west-1:488643450383:NotifySNS",
            Subject="Triggered Alarm " + data["DevEUI"],
            Message=expected_message
        )

    @staticmethod
    def parse_payload(body):
        try:
            payload = body["payload"]
            str_packet_id = payload[:2]

            if str_packet_id == "10":
                return {"timeStamp": body["timeStamp"], "DevEUI": body["DevEUI"], "GEO": extract_lat_long(payload)}
            elif str_packet_id == "02":
                return {"timeStamp": body["timeStamp"], "DevEUI": body["DevEUI"], "KA": extract_keep_alive(payload)}

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
        d = datetime.utcfromtimestamp((int(time) * 1000) / 1e3)
        json_date = str(d.isoformat()) + "Z"
        payload = sigfox_dic["query_params"]["data"]
        device_id = sigfox_dic["query_params"]["id"]

        virtual_tx = device_id + "-" + json_date
        hash_object = hashlib.sha256(virtual_tx.encode())
        hex_dig = hash_object.hexdigest()
        parsed_result = {"virtual_tx": hex_dig, "timeStamp": int(time), "time_json": json_date, "payload": payload,
         "DevEUI": device_id, "type": "SIGFOX"}

        if "test" in sigfox_dic["query_params"]:
            parsed_result["test"] = sigfox_dic["query_params"]["test"]

        return parsed_result
