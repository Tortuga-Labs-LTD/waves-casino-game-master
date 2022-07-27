import os
import roulette_processbets
import roulette_startend

job = os.environ.get('JOB')
if (job == 'processBetsService'):
    roulette_processbets.processBetsService()
elif (job == 'startEndService'):
    roulette_startend.startEndService()