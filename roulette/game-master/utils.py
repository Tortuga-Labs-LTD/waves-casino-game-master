from datetime import datetime, date, time, timezone
import json
import requests
import pywaves as pw

def getFee(gameMasterUrl, dappAddress, senderPublicKey, funcName, funcArguments, assetId):
    tx = {
        "feeAssetId": assetId,
        "type": 16,
        "payment": [],
        "dApp": dappAddress,
        "senderPublicKey": senderPublicKey,
        "call": {
            "function": funcName,
            "args": funcArguments
        },
        "fee": {}
    }
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    myobj =  json.dumps(tx)
    x = requests.post(gameMasterUrl + "/transactions/calculateFee", data = myobj, headers = headers)
    t = json.loads(x.text)
    return t['feeAmount']

def invokeScriptDynamicFee(gameMasterUrl, address, dappAddress, functionName, functionArguments, payments, feeAsset):
    assetId = None
    if (feeAsset != None and not feeAsset and feeAsset != ""):
        assetId = feeAsset
    feeCalculated = getFee(gameMasterUrl, dappAddress, address.publicKey, functionName, functionArguments, assetId)
    tx = address.invokeScript(dappAddress, functionName, functionArguments, payments, assetId, txFee=feeCalculated)
    return tx

def getLastLoaded(gameApiUrl, dappAddress):
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    x = requests.get(gameApiUrl + "/api/Activity/" + dappAddress + "/lastloaded", headers = headers)
    t = json.loads(x.text)
    return datetime.strptime(t['lastLoaded'],"%Y-%m-%dT%H:%M:%S.%fZ")
    