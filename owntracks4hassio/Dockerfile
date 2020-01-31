#ARG BUILD_FROM="alpine:latest"
ARG BUILD_FROM
FROM $BUILD_FROM
LABEL version="1.0" description="OwnTracks Recorder for Hass"
LABEL authors="Zooil Yang <me@zooil.com>"
MAINTAINER zooil <me@zooil.com>

ENV LANG C.UTF-8

# build with `docker build --build-arg recorder_version=x.y.z '
ARG recorder_version=0.8.3

COPY makeconf.sh entrypoint.sh recorder.tar.gz config.mk / 
COPY recorder.conf /etc/default/recorder.conf
COPY recorder-health.sh /usr/local/sbin/recorder-health.sh

ENV VERSION=$recorder_version

RUN apk add --no-cache --virtual .build-deps \
        curl-dev libconfig-dev make \
        gcc musl-dev mosquitto-dev wget \
    && apk add --no-cache \
        libcurl libconfig-dev mosquitto-dev lmdb-dev libsodium-dev lua5.2-dev \
    && mkdir -p /usr/local/source \
    && cd /usr/local/source \
    && mv /recorder.tar.gz ./ \
    && tar xzf recorder.tar.gz \
    && cd recorder-$VERSION \
    && mv /config.mk ./ \
    && make \
    && make install \
    && cd / \
    && chmod 755 /entrypoint.sh \
    && rm -rf /usr/local/source \
    && chmod 755 /usr/local/sbin/recorder-health.sh \
    && apk del .build-deps
RUN apk add --no-cache \
	curl jq

VOLUME ["/store", "/config"]

HEALTHCHECK CMD /usr/local/sbin/recorder-health.sh

ENTRYPOINT ["/entrypoint.sh"]
