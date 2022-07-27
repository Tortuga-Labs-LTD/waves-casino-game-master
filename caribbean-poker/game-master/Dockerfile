FROM python:3.8-slim-buster

WORKDIR /app

ENV PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
COPY requirements.txt requirements.txt
RUN apt-get update
RUN  apt-get --assume-yes  install python3-dev
RUN  apt-get --assume-yes  install gcc
RUN pip3 install -r requirements.txt
COPY . .

CMD [ "python3", "-m" , "game_master_runner.py"]