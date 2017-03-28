import os

from flask import Flask, jsonify, request
from simple_salesforce import Salesforce
from werkzeug.exceptions import BadRequest

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
@auth.verify_jwt(check=auth.verify_logged_in, optional=True)
def get_user_data(uid):
    contact = sf.Contact.get(uid)
    if request.authorization:
        return jsonify(
            only_keys(contact, app.config["PUBLIC_FIELDS"] + app.config["PRIVATE_FIELDS"]))
    else:
        return jsonify(only_keys(contact, app.config["PUBLIC_FIELDS"]))


@app.route('/api/users/<string:uid>', methods=['POST'])
@auth.verify_jwt(check=auth.verify_logged_in)
def update_user_data(uid):
    data = request.get_json()
    if "key" not in data:
        raise BadRequest("key property in request data is missing")
    if "value" not in data:
        raise BadRequest("value property in request data is missing")
    sf.Contact.update(uid, {data["key"]: data["value"]})
    return "User data updated"


if __name__ == '__main__':
    app.run()
