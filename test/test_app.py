"""
This script is for testing/calling in several different ways
functions from QRColorChecker modules.


@author: Eduard Cespedes Borràs
@mail: eduard@iot-partners.com
"""
import unittest
import hashlib

import dateutil

from chalicelib.server import Server
import sys
import json
from datetime import datetime

sys.path.append('../chalicelib')


class AppTest(unittest.TestCase):
    def setUp(self):
        self.sns_client = TestSNS()
        self.log = TestLog()
        self.dynamodb = TestDynamoDB()
        self.str_data = '{"DevEUI_uplink": {"Time": "2017-03-11T11:52:50.412+01:00","DevEUI": "0004A30B001C3306",' \
                        '"FPort": "7","FCntUp": "1","MType": "2","FCntDn": "2","payload_hex": "10bb17f18198100734",' \
                        '"mic_hex": "c00c1cfa","Lrcid": "00000127","LrrRSSI": "-64.000000","LrrSNR": "9.000000",' \
                        '"SpFact": "11","SubBand": "G1","Channel": "LC2","DevLrrCnt": "1","Lrrid": "08060412","Late":' \
                        ' "0","LrrLAT": "41.550377","LrrLON": "2.241691","Lrrs": {"Lrr": {"Lrrid": "08060412",' \
                        '"Chain": "0","LrrRSSI": "-64.000000","LrrSNR": "9.000000","LrrESP": "-64.514969"}},' \
                        '"CustomerID": "100001774",' \
                        '"CustomerData": {"alr":{"pro":"LORA/Generic","ver":"1"}},' \
                        '"ModelCfg": "0","DevAddr": "260113E2","AckRequested": "0",' \
                        '"rawMacCommands": "0703070307030703"}}'

    def test_parse_lora_json(self):
        jsonbody = json.loads(self.str_data)
        parsed_json = Server.parse_lora_json(self.str_data)

        time = jsonbody["DevEUI_uplink"]["Time"]
        payload = jsonbody["DevEUI_uplink"]["payload_hex"]
        device_id = jsonbody["DevEUI_uplink"]["DevAddr"]

        virtual_tx = device_id + "-" + time
        hash_object = hashlib.sha256(virtual_tx.encode())
        hex_dig = hash_object.hexdigest()

        dt = dateutil.parser.parse(time)
        strftime = dt.strftime("%s")
        time_millis = int(strftime) * 1000

        self.assertEqual(parsed_json["time_json"], time)
        self.assertEqual(parsed_json["timeStamp"], int(time_millis))
        self.assertEqual(parsed_json["payload"], payload)
        self.assertEqual(parsed_json["DevEUI"], device_id)
        self.assertEqual(parsed_json["type"], "LORA")
        self.assertEqual(parsed_json["extra"], json.dumps(jsonbody))
        self.assertEqual(parsed_json["virtual_tx"], hex_dig)

        # print(time + " deviceId: " + device_id + " payload: " + payload)
        #   str_packet_id = payload[:2]
        # print("packed_id: " + str_packet_id)

    def test_parse_sigfox(self):
        data_dic = {
            "context": {
                "httpMethod": "GET",
                "identity": {
                    "sourceIp": "127.0.0.1"
                },
                "resourcePath": "/sigfox"
            },
            "headers": {
                "accept": "*/*",
                "accept-encoding": "gzip, deflate",
                "connection": "keep-alive",
                "host": "localhost:8000",
                "user-agent": "HTTPie/0.9.8"
            },
            "method": "GET",
            "query_params": {
                "data": "10bb17f18198100734",
                "id": "260113E2",
                "time": "1515360218723"
            },
            "stage_vars": {},
            "uri_params": {}
        }

        parsed_dic = Server.parse_sigfox_dic(data_dic)

        d = datetime.utcfromtimestamp(int("1515360218723") / 1e3)
        json_date = str(d.isoformat()) + "Z"

        virtual_tx = "260113E2" + "-" + json_date
        hash_object = hashlib.sha256(virtual_tx.encode())
        hex_dig = hash_object.hexdigest()

        self.assertEqual(parsed_dic["time_json"], json_date)
        self.assertEqual(parsed_dic["timeStamp"], int("1515360218723"))
        self.assertEqual(parsed_dic["payload"], "10bb17f18198100734")
        self.assertEqual(parsed_dic["DevEUI"], "260113E2")
        self.assertEqual(parsed_dic["type"], "SIGFOX")
        self.assertEqual(parsed_dic["virtual_tx"], hex_dig)

    def test_publishing_data_to_SNS(self):
        data_to_publish = {
            "DevEUI": "260113E3",
            "extra": {
                "DevEUI_uplink": {
                    "CustomerID": "100001774",
                    "DevAddr": "260113E3"
                }
            },
            "payload": "010000beef",
            "timeStamp": 1499366509000,
            "time_json": "2017-07-06T18:41:49.51+02:00",
            "type": "LORA",
            "virtual_tx": "2dd66154468fa5d433420f5bad5d3f580f3dab46fa33e127ef69c511f641ae2f"
        }

        server = Server(None, self.sns_client, self.log)
        expected_message = json.dumps(data_to_publish)
        server.publish_data_store_device(data_to_publish)
        self.assertEqual(1, self.sns_client.return_published_times())
        self.assertEqual(expected_message, self.sns_client.return_message())
        self.assertEqual("arn:aws:sns:eu-west-1:488643450383:StoreDeviceData", self.sns_client.return_topicarn())

    def test_persist_data_to_DynamoDB(self):
        server = Server(self.dynamodb, None, self.log)
        expected_item = {
            'title': "The Big New Movie",
            'year': 2015,
            'info': {
                'plot': "Nothing happens at all.",
                'rating': "0"
            }
        }
        server.persist_data(expected_item)
        self.assertEqual(1, self.dynamodb.return_persisted_times())
        self.assertEqual(expected_item, self.dynamodb.return_persisted_item())


class TestLog:
    def __init__(self):
        self.message = ''
        self.logged = 0

    def debug(self, message):
        self.message = message
        self.logged += 1
        return message

    def return_message(self):
        return self.message

    def return_logging_times(self):
        return self.logged


class TestSNS:
    def __init__(self):
        self.Message = ''
        self.TopicArn = ''
        self.Subject = ''
        self.published = 0

    def publish(self, TopicArn, Subject, Message):
        self.Message = Message
        self.TopicArn = TopicArn
        self.Subject = Subject
        self.published += 1

    def return_topicarn(self):
        return self.TopicArn

    def return_message(self):
        return self.Message

    def return_published_times(self):
        return self.published


class TestDynamoDB:
    def __init__(self):
        self.Item = ''
        self.persisted = 0

    def put_item(self, Item):
        self.Item = Item
        self.persisted += 1

    def return_persisted_item(self):
        return self.Item

    def return_persisted_times(self):
        return self.persisted
