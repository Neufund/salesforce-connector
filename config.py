SF_INSTANCE = "eu11.salesforce.com"
SF_USERNAME = "remco+salesforce-api@neufund.org"

PUBLIC_FIELDS = ["LastName",
                 "FirstName",
                 "Name"]
PRIVATE_FIELDS = ["Phone",
                  "Fax",
                  "MobilePhone",
                  "Email",
                  "Ethereum_Address__c",
                  "KYC_Identification__c",
                  "KYC_Address__c",
                  "KYC_Submitted__c",
                  "KYC_Accepted__c",
                  "KYC_Rejected__c",
                  "KYC_Response__c"]
REQUIRED_ENV_CONFIG_FIELDS = ["SF_PASSWORD", "SF_TOKEN"]

MS2_AUDIENCE = "MS2"
LOGIN_ALGORITHM = "ES512"
PUB_KEY_PATH = "ec512.pub.pem"
ISSUER = "Neufund"

PUBLIC_ECDSA_KEY = None


def read_keys():
    global PUBLIC_ECDSA_KEY
    with open(PUB_KEY_PATH, "r") as publicKey:
        PUBLIC_ECDSA_KEY = publicKey.read()


read_keys()
