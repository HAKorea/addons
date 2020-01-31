#ARG BUILD_FROM="alpine:latest"
ARG BUILD_FROM
FROM $BUILD_FROM

ENV LANG C.UTF-8

# Copy data for add-on
COPY run.sh commax_homegateway.js /

# Install requirements for add-on
RUN apk add --no-cache jq npm make gcc g++ python linux-headers udev && \
    npm init -f && \
    npm install mqtt && \
    npm install serialport --build-from-source=serialport 

WORKDIR /share

RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
