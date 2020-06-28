#ARG BUILD_FROM="alpine:latest"
ARG BUILD_FROM
FROM $BUILD_FROM

ENV LANG C.UTF-8

# Copy data for add-on
COPY run.sh makeconf.sh rs485.py /

# Install requirements for add-on
RUN apk add --no-cache jq
RUN apk add --no-cache jq
RUN apk add --no-cache python3 py3-pip && \
        python3 -m pip install pyserial && \
        python3 -m pip install paho-mqtt

WORKDIR /share

RUN chmod a+x /makeconf.sh
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
