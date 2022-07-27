import pywaves as pw
import time
import logging
import yaml
import utils

def processBetsService():
    logger = logging.getLogger('Roulette Game Master Logger')

    with open("config.yml", "r") as ymlfile:
        cfg = yaml.safe_load(ymlfile)

    logging.basicConfig(format=cfg['logging']['format'], force=True)
    logger.setLevel(cfg['logging']['level'])

    pw.setNode(cfg["gamemaster"]["nodeurl"], cfg["gamemaster"]["chain"], cfg["gamemaster"]["chainid"])
    address = pw.Address(seed=cfg["gamemaster"]["seed"])
    dappAddress = cfg["dappAddress"]
    oracle = pw.Oracle(oracleAddress = dappAddress)

    logger.info("Found job game Process Bets")
    while(True):
        logger.info("Starting checking bets...")
        try:
            totalBets = oracle.getData('G_TOTALBETS')
            processedBets = oracle.getData('G_PROCESSEDBETS')
            betsToProcess = totalBets - processedBets
            if(betsToProcess > 0):
                logger.info("Found " + str(betsToProcess) + " to process.")
                for i in range(totalBets - processedBets):
                    processBetTx = utils.invokeScriptDynamicFee(cfg["gamemaster"]["nodeurl"], address, dappAddress, 'processNextBet', [], [], oracle.getData("G_TOKENID"))
                    logger.info("Processed bet")
                time.sleep(30)
            else:
                logger.info("No bets found to process, sleeping for 3 seconds.")
                time.sleep(3)
        except Exception as e:
            logger.error("An exception occurred. " + str(e))
