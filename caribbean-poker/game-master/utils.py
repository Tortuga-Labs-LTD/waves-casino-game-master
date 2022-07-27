import time
import base64
import base58
import random
from Crypto.PublicKey import RSA
from Crypto.Signature.pkcs1_15 import PKCS115_SigScheme
from Crypto.Hash import SHA256
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from datetime import datetime, date, time, timezone
import json
import requests
import pywaves as pw


def filterStateChange(stateChanges, key): 
    return list(filter(lambda x: x['key'] == key, stateChanges))[0]

def awaitTxFinish(pw, txId):
    txDetails = pw.tx(txId)
    total = 0
    while('error' in txDetails and txDetails['error'] == 311 and total < 60):
        time.sleep(1)
        txDetails = pw.tx(txId)
        total += 1
    return txDetails

def generateSha256Signature(signer, normalString):
    hash = SHA256.new(normalString.encode())
    return base64.b64encode(signer.sign(hash)).decode('ascii')

def aesEncryptString(key, normalString): 
    BS = AES.block_size
    pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)
    keyEncoded = key.encode()
    iv = get_random_bytes(16)
    aes = AES.new(keyEncoded, AES.MODE_CBC, iv)
    paddedString = pad(normalString)
    return base64.urlsafe_b64encode(iv + aes.encrypt(paddedString.encode())).decode()

def aesUnencryptString(key, encryptedString): 
    BS = AES.block_size
    unpad = lambda s : s[:-ord(s[len(s)-1:])]
    enc = base64.urlsafe_b64decode(encryptedString.encode())
    iv = enc[:BS]
    cipher = AES.new(key.encode(), AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(enc[BS:])).decode()

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
    