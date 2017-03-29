import json
import unittest
from datetime import timedelta
from json.decoder import JSONDecodeError

import jwt

from auth import _get_claims
from server import app

REMCO_ADDRESS = "0x45aD9DF0526109Ba95CA6aA099833c04C9220f19"
REMCO_SALESFORCE_ID = "0030Y00000AyoFCQAZ"
REMCO_DATA = {'Email': None,
              'Ethereum_Address__c': '0x45aD9DF0526109Ba95CA6aA099833c04C9220f19',
              'Fax': None,
              'FirstName': 'Remco',
              'KYC_Accepted__c': False,
              'KYC_Address__c': None,
              'KYC_Document__c': None,
              'KYC_Rejected__c': False,
              'KYC_Response__c': None,
              'KYC_Submitted__c': False,
              'LastName': 'Bloemen',
              'MobilePhone': None,
              'Name': 'Remco Bloemen',
              'Phone': None}
VITALIK_SALESFORCE_ID = "0030Y00000DvyvvQAB"
VITALIK_DATA = {'FirstName': 'Vitalik',
                'LastName': 'Buterin',
                'Name': 'Vitalik Buterin'}
NON_EXISTING_ID = "90630000000h1PpAAI"


class SalesforceTest(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.token = self._login(REMCO_ADDRESS)

    def _login(self, address):
        payload = {**{"address": address}, **_get_claims(app.config['MS2_AUDIENCE'],
                                                         timedelta(days=1))}
        with open("ec512.prv.pem", "r") as privateKey:
            PRIVATE_ECDSA_KEY = privateKey.read()
        return jwt.encode(payload, PRIVATE_ECDSA_KEY,
                          algorithm=app.config['LOGIN_ALGORITHM']).decode("utf-8")

    def getData(self, uid):
        data = self.app.get(
            '/api/users/' + uid,
            headers={"Authorization": "JWT {}".format(self.token)},
            content_type='application/json'
        ).data.decode("utf-8")
        try:
            data = json.loads(data)
        except JSONDecodeError:
            pass
        return data

    def testGetSomeonesData(self):
        self.assertDictEqual(VITALIK_DATA, self.getData(VITALIK_SALESFORCE_ID))

    def testNonExistingData(self):
        self.assertDictEqual({'code': 404, 'message': 'User 90630000000h1PpAAI not found'},
                             self.getData(NON_EXISTING_ID))

    def testGetMyData(self):
        self.assertDictEqual(REMCO_DATA, self.getData(REMCO_SALESFORCE_ID))

    def updateData(self, uid, data):
        data = self.app.post(
            '/api/users/' + uid,
            data=json.dumps(data),
            headers={"Authorization": "JWT {}".format(self.token)},
            content_type='application/json'
        ).data.decode("utf-8")
        try:
            data = json.loads(data)
        except JSONDecodeError:
            pass
        return data

    def testUpdateDataIsReversible(self):
        self.assertEqual("User data updated",
                         self.updateData(REMCO_SALESFORCE_ID, {"FirstName": "UpdatedName"}))
        self.assertEqual("UpdatedName", self.getData(REMCO_SALESFORCE_ID)["FirstName"])
        self.assertEqual("User data updated",
                         self.updateData(REMCO_SALESFORCE_ID, {"FirstName": "Remco"}))
        self.assertDictEqual(REMCO_DATA, self.getData(REMCO_SALESFORCE_ID))
