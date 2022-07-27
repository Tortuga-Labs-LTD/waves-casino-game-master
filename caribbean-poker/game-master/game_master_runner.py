import os
import processbets
import startend

job = os.environ.get('JOB')
if (job == 'processBetsService'):
    processbets.processBetsService()
elif (job == 'startEndService'):
    startend.startEndService()