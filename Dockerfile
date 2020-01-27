#ARG BUILD_FROM="alpine:latest"
ARG BUILD_FROM
FROM $BUILD_FROM

ENV LANG C.UTF-8

# Install requirements for add-on
RUN apk add --no-cache jq curl openssh-client sshpass
RUN apk add --no-cache -X http://dl-cdn.alpinelinux.org/alpine/edge/testing motion

# Copy data for add-on
COPY run.sh /
COPY scripts /var/tmp/scripts
COPY motion.conf /etc/motion/

WORKDIR /data

RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
