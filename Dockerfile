FROM python:3

ENV LANG C.UTF-8

RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install pyserial
RUN python3 -m pip install paho-mqtt

WORKDIR /share

COPY . /srv
RUN chmod a+x /srv/run_addon.sh

CMD [ "/srv/run_addon.sh" ]
