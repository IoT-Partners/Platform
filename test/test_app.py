"""
This script is for testing/calling in several different ways
functions from QRColorChecker modules.


@author: Eduard Cespedes Borràs
@mail: eduard@iot-partners.com
"""

import unittest
from chalicelib.server import Server
import sys
import json

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
        server = Server(None, None, self.log)
        jsonbody = json.loads(self.str_data)
        parsed_json = server.parse_lora_json(jsonbody)

        time = jsonbody["DevEUI_uplink"]["Time"]
        payload = jsonbody["DevEUI_uplink"]["payload_hex"]
        device_id = jsonbody["DevEUI_uplink"]["DevAddr"]

        self.assertEquals(parsed_json["time"], time)
        self.assertEquals(parsed_json["payload"], payload)
        self.assertEquals(parsed_json["device_id"], device_id)
        self.assertEquals(parsed_json["type"], "LORA")
        self.assertEquals(parsed_json["extra"], jsonbody)

    def test_publishing_data_to_SNS(self):
        server = Server(None, self.sns_client, self.log)
        expected_message = "Good news everyone!"
        server.publish_data()
        self.assertEqual(1, self.sns_client.return_published_times())
        self.assertEqual(expected_message, self.sns_client.return_message())

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
        server.persist_data()
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
