#ARG BUILD_FROM="alpine:latest"
ARG BUILD_FROM
FROM $BUILD_FROM

ENV LANG C.UTF-8

# Copy data for add-on
COPY run.sh commax_homegateway.js /

# Install requirements for add-on
RUN apk add --no-cache jq npm

WORKDIR /data

RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
