import json

from web3 import HTTPProvider, Web3

KYC_ARTIFACTS_PATH = "Contracts/build/contracts/KYCRegistery.json"


def create_contract_from_truffle_artifacts(path, web3):
    from server import app
    with open(path) as contract:
        kyc_spec_json = json.load(contract)
    abi = kyc_spec_json["abi"]
    address = kyc_spec_json["networks"][web3.version.network]["address"]
    return web3.eth.contract(abi, address)


def get_kyc_hash_for_address(address):
    from server import app
    web3 = Web3(HTTPProvider(endpoint_uri=app.config["WEB3_ENDPOINT"]))
    KYCRegistry = create_contract_from_truffle_artifacts(KYC_ARTIFACTS_PATH, web3)
    return KYCRegistry.call().hash_of(address)
