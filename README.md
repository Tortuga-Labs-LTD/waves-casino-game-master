
# Waves Casino Game Master and Smart Contract

This project contains the logic to run multiple casino games on the Waves blockchain protocol. Each game uses a Smart Contract to encapsulate the main logic and a Game Master (Oracle) that produces a sequence to randomize the game.

Both components are highly interconnected between each other, both are needed to run the game; each of them has a separate Waves account.

## How to run each of the games
1. RSA certificate (for all games, it could be shared across games)
    1. Create a RSA private and public key
    1. The public key will be used in the Smart Contract. This setting is customizable and can be editted after publishing the Smart Contract by calling the following method `setParameter('changeRSA',<your-rsa-public-key-here>)`
        1. Please note it could be different in other games, e.g. caribbean poker (you might need to change `let RSAPUBLIC = fromBase64String('base64:RSAPUBLIC'))` instead)
    1. Enter the private key in the setting `signingcertificate` located in `game-master/config.yml`
1. Waves accounts: Game Master and Smart Contract (for all the games, one per game)
    1. Identify a Waves account as the Game Master
    1. Copy the public key of the Game Master account to the value of the variable `gameMasterPublicKey` om the Smart Contract, then replace `<game-master-public-key>` with the Game Master public key copied in previous step
    1. Copy the seed of the Game Master account to the setting `seed` located in `game-master/config.yml`
    1. Identify a Waves account as the Smart Contract
    1. Copy the Smart Contract account address to the setting `dappAddress` located in `game-master/config.yml`
1. Copy the game API URL account address to the setting `gameapi/url` located in `game-master/config.yml`. If there is no API to run, leave this setting blank (only needed for some games, e.g. roulette)
1. Create the Docker container image
1. Publish Smart Contract, go to the development environment [Waves IDE](https://waves-ide.com/) and follow the documentation
1. Initialize the Smart Contract by calling `initGame()` in the Smart Contract dApp. Note: this function can only be called from the Game Master
1. Run step 1.2, call the following method in the Smart Contract `setParameter('changeRSA',<your-rsa-public-key-here>)` (only needed for some games, e.g. roulette)
1. Run two Docker containers. There are two services that run independently from each other: a) the start-end service and b) the process-bets service. Use the docker environment `JOB` when running the container with `startEndService` or `processBetsService` to speficy which service to run
    - Start-end service: it is used to produce a sequence (before any bets are placed) which is stored on the chain, then can be use to randomize the result. Note the Game Master is the only one who has the private key can sign the transaction.
    - Process-bets service: it is used to process all the bets sequentially after a game is finished
1. Have fun!
