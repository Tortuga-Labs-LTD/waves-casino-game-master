from email import utils
import pywaves as pw
import time
import logging
import yaml
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
from  utils import generateSha256Signature, aesEncryptString, aesUnencryptString, invokeScriptDynamicFee

def processBetsService():
    
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

    signer = PKCS115_SigScheme(privateKey)
    oracle = pw.Oracle(oracleAddress = dappAddress)

    while(True):
        try:
            dealersQueue = oracle.getData('G_DEALERQUEUE')
            if len(dealersQueue) > 0:
                allInQueue = dealersQueue.split(",")[1:]

                for game in allInQueue:
                    
                    gameState = oracle.getData('G_'+game+'_STATE')

                    if gameState == 1:
                        logger.info("Found " + game + " needs first deal.")
                        card0 = aesUnencryptString(aesKey, oracle.getData('G_'+ str(game) + "_CARDSIGNATURE_0").split(" ")[1])
                        card1 = aesUnencryptString(aesKey, oracle.getData('G_'+ str(game) + "_CARDSIGNATURE_1").split(" ")[1])
                        card2 = aesUnencryptString(aesKey, oracle.getData('G_'+ str(game) + "_CARDSIGNATURE_2").split(" ")[1])
                        allCards = card0.split("+")[2:]
                        allCards.append(card1.split("+")[2])
                        allCards.sort(key=lambda x: int(x.split("/")[0]), reverse=False)
                        appended = "+".join(allCards)

                        tx = invokeScriptDynamicFee(cfg["gamemaster"]["nodeurl"], address ,dappAddress, 'revealCards',
                        [
                        {"type": "integer", "value":  int(game) },
                        {"type": "string", "value": card0}, 
                        {"type": "string", "value": card1},
                        {"type": "string", "value": card2},
                        {"type": "string", "value": appended}
                        ], [], "")
                        if 'error' in tx:
                            logger.error("Failed to create game with error " + tx['message'])
                        else:
                            logger.info("Continued game " + game)
                    elif gameState == 3:
                        logger.info("Found " + game + " needs results shown.")
                        card2 = aesUnencryptString(aesKey, oracle.getData('G_'+ str(game) + "_CARDSIGNATURE_2").split(" ")[1])
                        card3 = aesUnencryptString(aesKey, oracle.getData('G_'+ str(game) + "_CARDSIGNATURE_3").split(" ")[1])
                        allCards = card3.split("+")[2:]
                        allCards.append(card2.split("+")[2])
                        allCards.sort(key=lambda x: int(x.split("/")[0]), reverse=False)
                        appended = "+".join(allCards)

                        tx = invokeScriptDynamicFee(cfg["gamemaster"]["nodeurl"], address, dappAddress, 'revealResults', 
                        [
                        {"type": "integer", "value":  int(game) },
                        {"type": "string", "value": card3},
                        {"type": "string", "value": appended}
                        ], [], "")
                        if 'error' in tx:
                            logger.error("Failed to end game with error " + tx['message'])
                        else:
                            logger.info("Ended game " + game)
                logger.info("Finished all in queue")
            else:
                logger.info("No games in queue")
                
        except Exception as e:
            logger.error("critical error, restarting from scratch. " + str(e))