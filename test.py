import json
import unittest
from datetime import timedelta
from json.decoder import JSONDecodeError

import jwt

from auth import _get_claims
from server import app

REMCO_ADDRESS = "0x45aD9DF0526109Ba95CA6aA099833c04C9220f19"
REMCO_SALESFORCE_ID = "0030Y00000AyoFCQAZ"
REMCO_DATA = {'Email': "remco@neufund.org",
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

ID_NOT_FOUND = {'code': 404, 'message': 'User 90630000000h1PpAAI not found'}
EMAIL_UPDATE_FORBIDDEN = {'code': 403, 'message': "2FA users can't update their emails"}


class SalesforceTest(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.two_factor_token = self._login(REMCO_ADDRESS, "2FA")
        self.neukey_token = self._login(REMCO_ADDRESS, "neukey")

    def _login(self, address, login_method):
        payload = {**{"address": address, "login_method": login_method},
                   **_get_claims(app.config['MS2_AUDIENCE'],
                                 timedelta(days=1))}
        with open("ec512.prv.pem", "r") as privateKey:
            PRIVATE_ECDSA_KEY = privateKey.read()
        return jwt.encode(payload, PRIVATE_ECDSA_KEY,
                          algorithm=app.config['LOGIN_ALGORITHM']).decode("utf-8")

    def getData(self, uid, token):
        data = self.app.get(
            '/api/users/' + uid,
            headers={"Authorization": "JWT {}".format(token)},
            content_type='application/json'
        ).data.decode("utf-8")
        try:
            data = json.loads(data)
        except JSONDecodeError:
            pass
        return data

    def testGetSomeonesData(self):
        self.assertDictEqual(VITALIK_DATA,
                             self.getData(VITALIK_SALESFORCE_ID, self.two_factor_token))

    def testNonExistingData(self):
        self.assertDictEqual(ID_NOT_FOUND,
                             self.getData(NON_EXISTING_ID, self.two_factor_token))

    def testGetMyData(self):
        self.assertDictEqual(REMCO_DATA, self.getData(REMCO_SALESFORCE_ID, self.two_factor_token))

    def updateData(self, uid, data, token):
        data = self.app.post(
            '/api/users/' + uid,
            data=json.dumps(data),
            headers={"Authorization": "JWT {}".format(token)},
            content_type='application/json'
        ).data.decode("utf-8")
        try:
            data = json.loads(data)
        except JSONDecodeError:
            pass
        return data

    def testUpdateDataIsReversible(self):
        self.assertEqual("User data updated",
                         self.updateData(REMCO_SALESFORCE_ID, {"FirstName": "UpdatedName"},
                                         self.two_factor_token))
        self.assertEqual("UpdatedName",
                         self.getData(REMCO_SALESFORCE_ID, self.two_factor_token)["FirstName"])
        self.assertEqual("User data updated",
                         self.updateData(REMCO_SALESFORCE_ID, {"FirstName": "Remco"},
                                         self.two_factor_token))
        self.assertDictEqual(REMCO_DATA, self.getData(REMCO_SALESFORCE_ID, self.two_factor_token))

    def test2FAUsersCantUpdateEmail(self):
        self.assertEqual(EMAIL_UPDATE_FORBIDDEN,
                         self.updateData(REMCO_SALESFORCE_ID, {"Email": "some@email.com"},
                                         self.two_factor_token))
        self.assertDictEqual(REMCO_DATA, self.getData(REMCO_SALESFORCE_ID, self.two_factor_token))

    def testLedgerUsersCanUpdateEmail(self):
        self.assertEqual("User data updated",
                         self.updateData(REMCO_SALESFORCE_ID, {"Email": "remco@neufund.org"},
                                         self.neukey_token))
