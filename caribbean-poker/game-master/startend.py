import base64
from datetime import date, datetime, timedelta
import os
import base58
from Crypto.PublicKey import RSA
from Crypto.Signature.pkcs1_15 import PKCS115_SigScheme
from Crypto.Hash import SHA256
import pywaves as pw
import random
import time
import logging
import yaml
from  utils import generateSha256Signature, aesEncryptString, invokeScriptDynamicFee

def filterStateChange(stateChanges, key): 
    return list(filter(lambda x: x['key'] == key, stateChanges))[0]

def awaitTxFinish(txId):
    txDetails = pw.tx(txId)
    total = 0
    while('error' in txDetails and txDetails['error'] == 311 and total < 60):
        time.sleep(1)
        txDetails = pw.tx(txId)
        total += 1
    return txDetails

def startEndService():
    
    logger = logging.getLogger('Caribbean Poker Logger')
    with open("config.yml", "r") as ymlfile:
        cfg = yaml.safe_load(ymlfile)

    pw.setNode(cfg["gamemaster"]["nodeurl"], 'turtlenetwork', cfg["gamemaster"]["chainid"])
    privateKey = RSA.import_key(cfg["gamemaster"]["signingcertificate"])
    seed= cfg["gamemaster"]["seed"]
    address = pw.Address(seed=seed)
    logging.basicConfig(format=cfg['logging']['format'], force=True)
    logger.setLevel(cfg['logging']['level'])
    dappAddress = cfg["dappAddress"]
    aesKey = cfg["gamemaster"]["encryptionKey"]
    gameToPrepare = cfg["gamemaster"]["gamesToPrepare"]
    signer = PKCS115_SigScheme(privateKey)
    oracle = pw.Oracle(oracleAddress = dappAddress)

    while(True):
        try:
            deck = [
                "2/S",	"2/C",	"2/H",	"2/D",
                "3/S",	"3/C",	"3/H",	"3/D",
                "4/S",	"4/C",	"4/H",	"4/D",
                "5/S",	"5/C",	"5/H",	"5/D",
                "6/S",	"6/C",	"6/H",	"6/D",
                "7/S",	"7/C",	"7/H",	"7/D",
                "8/S",	"8/C",	"8/H",	"8/D",
                "9/S",	"9/C",	"9/H",	"9/D",
                "10/S",	"10/C",	"10/H",	"10/D",
                "11/S",	"11/C",	"11/H",	"11/D",
                "12/S",	"12/C",	"12/H",	"12/D",
                "13/S",	"13/C",	"13/H",	"13/D",
                "14/S",	"14/C",	"14/H",	"14/D"
            ]

            random.shuffle(deck)
            totalSetupGames = oracle.getData('G_SETUPGAMESCOUNTER')
            totalUsedGames = oracle.getData('G_USEDGAMESCOUNTER')

            if totalSetupGames - totalUsedGames < gameToPrepare:
                nextGame = totalSetupGames + 1
                logger.info("Not enough games available, available: " +str(totalSetupGames) + " used: "+ str(totalUsedGames) + "setting up game" + str(nextGame))
                
                header = "D/" + dappAddress + "+G/" + str(nextGame) 
                cardSet0 = header + "+" + deck[0] + "+" + deck[1] + "+" + deck[2] + "+" + deck[3]
                cardSet1 = header + "+" + deck[4]
                cardSet2 = header + "+" + deck[5]
                cardSet3 = header + "+" + deck[6] + "+" + deck[7] + "+" + deck[8] + "+" + deck[9]

                tx = invokeScriptDynamicFee(cfg["gamemaster"]["nodeurl"],address,dappAddress, 'setupGame', 
                [
                {"type": "integer", "value":  nextGame },
                {"type": "string", "value": generateSha256Signature(signer, cardSet0) + " " +  aesEncryptString(aesKey, cardSet0)}, 
                {"type": "string", "value": generateSha256Signature(signer, cardSet1) + " " +  aesEncryptString(aesKey, cardSet1) }, 
                {"type": "string", "value": generateSha256Signature(signer, cardSet2) + " " +  aesEncryptString(aesKey, cardSet2) }, 
                {"type": "string", "value": generateSha256Signature(signer, cardSet3) + " " +  aesEncryptString(aesKey, cardSet3) }], [], "")
                if 'error' in tx:
                    logger.error("Failed to create game with error " + tx['message'])
                else:
                    logger.info("Created game " + str(nextGame))
            else:
                logger.info("Enough games are prepared available: " +str(totalSetupGames) + " used: "+ str(totalUsedGames))

        except Exception as e:
            logger.error("critical error, restarting from scratch. " + str(e))