import base64
from datetime import date, datetime, timedelta
import base58
from Crypto.PublicKey import RSA
from Crypto.Signature.pkcs1_15 import PKCS115_SigScheme
from Crypto.Hash import SHA256
import pywaves as pw
import random
import time
import logging
import yaml
import utils

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
    logger = logging.getLogger('Roulette Game Master Logger')

    with open("config.yml", "r") as ymlfile:
        cfg = yaml.safe_load(ymlfile)

    logging.basicConfig(format=cfg['logging']['format'], force=True)
    logger.setLevel(cfg['logging']['level'])

    blocksPerRound = cfg["gamemaster"]["blocksperround"]
    pw.setNode(cfg["gamemaster"]["nodeurl"], cfg["gamemaster"]["chain"], cfg["gamemaster"]["chainid"])
    privateKey = RSA.import_key(cfg["gamemaster"]["signingcertificate"])
    address = pw.Address(seed=cfg["gamemaster"]["seed"])
    dappAddress = cfg["dappAddress"]
    gameAPIUrl = cfg["gameapi"]["url"]
    elapsedTimeBetweenChecksInSeconds = cfg["gameapi"]["elapsedtimebetweenchecksinseconds"]
    timeToSleepInSeconds = cfg["gameapi"]["timetosleepinseconds"]
    signer = PKCS115_SigScheme(privateKey)
    oracle = pw.Oracle(oracleAddress = dappAddress)
    logger.info("Starting main loop")

    while(True):
        try:
            try:
                if gameAPIUrl:
                    logger.info("Checking if need to start new game")
                    lastupdated = utils.getLastLoaded(gameAPIUrl, dappAddress) + timedelta(seconds=elapsedTimeBetweenChecksInSeconds)
                    if (datetime.utcnow() > lastupdated):
                        time.sleep(timeToSleepInSeconds)
                        continue                

                logger.info("Starting new game")
                tokenId =  oracle.getData("G_TOKENID")
                randomString =''.join(random.choices('123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz', k=34))    
                tx = utils.invokeScriptDynamicFee(cfg["gamemaster"]["nodeurl"], address, dappAddress, 'startGame', [{"type": "string", "value": randomString }, {"type": "integer", "value": blocksPerRound}], [], tokenId)
                txDetails = awaitTxFinish(tx['id'])

                stateChanges = pw.stateChangeForTx(tx['id'])['stateChanges']['data']
                gameNumber = filterStateChange(stateChanges, 'G_GAMESCOUNTER')
                sumSha = filterStateChange(stateChanges, 'G_'+str(gameNumber['value'])+'_SUMSHA')
                endHeight = filterStateChange(stateChanges, 'G_'+str(gameNumber['value'])+'_ENDHEIGHT')
                startHeight = txDetails['height']
                currentHeight = pw.height()
                logger.info("Started game " + str(gameNumber['value']))

                while(currentHeight < endHeight['value']):
                    logger.debug("Awaiting height to increase, current height is " + str(currentHeight) + ", game will end at height " + str( endHeight['value']))
                    currentHeight = pw.height()
                    time.sleep(5)

                time.sleep(5)
                hash = SHA256.new(base58.b58decode(sumSha['value']))
                signature = base64.b64encode(signer.sign(hash)).decode('ascii')

                endtx = utils.invokeScriptDynamicFee(cfg["gamemaster"]["nodeurl"], address, dappAddress, 'endGame', [{"type": "string", "value": signature},{"type": "integer", "value": gameNumber['value'] }], [], tokenId)
                
                while('error' in endtx and endtx['error'] == 306):
                    time.sleep(1)
                    logger.debug("Waiting on game to end still...")
                    endtx = utils.invokeScriptDynamicFee(cfg["gamemaster"]["nodeurl"], address, dappAddress, 'endGame', [{"type": "string", "value": signature},{"type": "integer", "value": gameNumber['value'] }], [], tokenId)
                logger.info("game has ended.")
                endtxDetails = awaitTxFinish(endtx['id'])
                sc = pw.stateChangeForTx(endtx['id'])
                endstateChanges = pw.stateChangeForTx(endtx['id'])['stateChanges']['data']

                randomNumberGenerated = filterStateChange(endstateChanges, 'G_'+str(gameNumber['value'])+'_RESULT')
                logger.info("Generated random number " + str(randomNumberGenerated['value']) + " for game " + str(gameNumber['value']))
            except Exception as exception1:
                logger.error("Encountered error, try to end last game and restarting... ")
                tokenId =  oracle.getData("G_TOKENID")
                gameNumber = oracle.getData("G_GAMESCOUNTER")
                sumSha = oracle.getData('G_'+str(gameNumber)+'_SUMSHA')
                hash = SHA256.new(base58.b58decode(str(sumSha)))
                signature = base64.b64encode(signer.sign(hash)).decode('ascii')

                currentHeight = pw.height()
                endHeight = oracle.getData('G_'+str(gameNumber)+'_ENDHEIGHT')

                while(currentHeight < endHeight):
                    logger.debug("Awaiting height to increase, current height is " + str(currentHeight) + ", game will end at height " + str( endHeight))
                    currentHeight = pw.height()
                    time.sleep(5)
                endtx = utils.invokeScriptDynamicFee(cfg["gamemaster"]["nodeurl"], address, dappAddress, 'endGame', [{"type": "string", "value": signature},{"type": "integer", "value": gameNumber }], [], tokenId)
                endtxDetails = awaitTxFinish(endtx['id'])
        except Exception as e:
            logger.error("critical error, restarting from scratch. " + str(e)) 
