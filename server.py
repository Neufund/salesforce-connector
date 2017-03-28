import os

from flask import Flask, jsonify
from simple_salesforce import Salesforce

import auth

app = Flask(__name__)
app.config.from_pyfile('config.py')

for key in app.config["REQUIRED_ENV_CONFIG_FIELDS"]:
    if key not in os.environ:
        raise EnvironmentError("Required env variable {} missing".format(key))

app.config.from_mapping(os.environ)

sf = Salesforce(
    instance=app.config["SF_INSTANCE"],
    username=app.config["SF_USERNAME"],
    password=app.config["SF_PASSWORD"],
    security_token=app.config["SF_TOKEN"]
)


def only_keys(data, keys):
    return {key: data[key] for key in data if key in keys}


@app.route('/api/users/<string:uid>', methods=['GET'])
def get_public_user_data(uid):
    contact = sf.Contact.get(uid)
    return jsonify(only_keys(contact, app.config["PUBLIC_FIELDS"]))


@app.route('/api/users/<string:uid>/private', methods=['GET'])
@auth.verify_jwt(check=auth.verify_logged_in)
def get_private_user_data(uid):
    contact = sf.Contact.get(uid)
    return jsonify(only_keys(contact, app.config["PUBLIC_FIELDS"] + app.config["PRIVATE_FIELDS"]))


if __name__ == '__main__':
    app.run()


# pprint(sf.Contact.get_by_custom_id("Ethereum_Address__c", "PO"))
# pprint(sf.query_all("SELECT Id FROM Contact"))
# pprint(sf.query("SELECT Id, Name, Email, Company, Phone "
#                 "FROM Lead WHERE EthereumAddress__c = '0xa57Da36D823976D21B8A6e1c584f17FCB4BF116a'"))

# pprint(sf.query("UPDATE Lead  "
#                 "SET Name='Remco' "
#                 "WHERE EthereumAddress__c = '0xa57Da36D823976D21B8A6e1c584f17FCB4BF116a'"))
# pprint(sf.Lead.describe())
# pprint(sf.Lead.describe_layout(ID))
# pprint(sf.Lead.get(ID))
# pprint(sf.Contact.update(ID, {"Ethereum_Address__c": "PO"}))
# pprint(sf.Lead.create({"Name": "Leonid"}))
