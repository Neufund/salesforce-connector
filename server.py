import hashlib
import os
from base64 import b64encode

from flask import Flask, jsonify, request
from simple_salesforce import Salesforce, SalesforceResourceNotFound
from werkzeug.exceptions import BadRequest, Forbidden, NotFound
from werkzeug.utils import secure_filename

import auth
from kyc import get_kyc_hash_for_address

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
@auth.verify_jwt(check=auth.verify_logged_in)
def get_user_data(uid):
    try:
        contact = sf.Contact.get(uid)
    except SalesforceResourceNotFound:
        raise NotFound("User {} not found".format(uid))
    if contact["Ethereum_Address__c"] == request.authorization["address"]:
        # Request for own data
        return jsonify(
            only_keys(contact, app.config["PUBLIC_FIELDS"] + app.config["PRIVATE_FIELDS"]))
    else:
        # Request for someone's data
        return jsonify(only_keys(contact, app.config["PUBLIC_FIELDS"]))


@app.route('/api/users/<string:uid>', methods=['POST'])
@auth.verify_jwt(check=auth.verify_logged_in)
def update_user_data(uid):
    try:
        contact = sf.Contact.get(uid)
    except SalesforceResourceNotFound:
        raise NotFound("User {} not found".format(uid))
    if contact["Ethereum_Address__c"] != request.authorization["address"]:
        raise Forbidden("You're only allowed to modify your own data")
    data = request.get_json()
    if "Email" in data:
        if request.authorization["login_method"] == "2FA":
            raise Forbidden("2FA users can't update their emails")
    sf.Contact.update(uid, data)
    return "User data updated"


def _allowed_file(filename):
    _, extension = os.path.splitext(filename)
    return extension.lower() in app.config["ALLOWED_EXTENSIONS"]


@app.route('/api/users/<string:uid>/kyc', methods=['POST'])
@auth.verify_jwt(check=auth.verify_logged_in)
def submit_kyc(uid):
    # check if the post request has the file part
    if 'file' not in request.files:
        raise BadRequest("No file part")
    file = request.files['file']
    # if user does not select file, browser also
    # submit a empty part without filename
    if file.filename == '':
        raise BadRequest("No selected file")
    if not _allowed_file(file.filename):
        raise BadRequest("Wrong file extension")
    filename = secure_filename(file.filename)
    file_content = file.read()
    file_content_hash = hashlib.sha3_256(file_content).hexdigest()
    if file_content_hash != get_kyc_hash_for_address(request.authorization["address"]):
        raise Forbidden("KYC hash doesn't match the one in the contract")
    file_content_base64 = b64encode(file_content).decode("utf-8")
    sf.Attachment.create(
        {"Body": file_content_base64, "ParentId": uid, "Name": filename,
         "ContentType": file.content_type})
    return file_content_hash


@app.errorhandler(403)
def forbidden(ex):
    return jsonify({"code": 403, "message": ex.description}), 403


@app.errorhandler(404)
def not_found(ex):
    return jsonify({"code": 404, "message": ex.description}), 404


if __name__ == '__main__':
    app.run()
