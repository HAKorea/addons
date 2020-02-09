#ARG BUILD_FROM=multiarch/debian-debootstrap:amd64-stretch
ARG BUILD_FROM
FROM $BUILD_FROM

# Install packages
RUN apt-get update
RUN apt-get install -y jq tzdata python3 python3-dev python3-pip \
        python3-six python3-pyasn1 libportaudio2 alsa-utils \
        portaudio19-dev libffi-dev libssl-dev libmpg123-dev
RUN pip3 install --upgrade pip
COPY requirements.txt /tmp
#ADD .asoundrc ascii2utf8.sh /root/
ADD ascii2utf8.sh /root/
RUN mkdir /root/.config && mkdir /root/.config/google-assistant-library

WORKDIR /tmp
RUN pip3 install -r requirements.txt
RUN pip3 install --upgrade six
RUN pip3 install --no-cache-dir google-assistant-library google-auth \
        requests_oauthlib cherrypy flask flask-jsonpify flask-restful \
        grpcio google-assistant-grpc google-auth-oauthlib \
        wheel google-assistant-sdk[samples] pyopenssl
RUN apt-get clean -y
RUN rm -rf /var/lib/apt/lists/*

ENV PYTHONIOENCODING utf-8

# Copy data
COPY run.sh /
COPY *.py /

RUN chmod a+x /root/ascii2utf8.sh
RUN chmod a+x /run.sh

WORKDIR /share

ENTRYPOINT [ "/run.sh" ]
