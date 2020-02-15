#ARG BUILD_FROM=multiarch/debian-debootstrap:amd64-stretch
ARG BUILD_FROM
FROM $BUILD_FROM
ENV DEBIAN_FRONTEND noninteractive
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

RUN pip3 install --upgrade flask flask-jsonpify flask-restful grpcio  \
        setuptools wheel pyopenssl
RUN pip3 install --no-cache-dir \
        cherrypy==18.1.0 \
        google-assistant-grpc==0.2.1 \
        google-assistant-library==1.0.0 \
        six==1.12.0 \
        google-assistant-sdk==0.5.1 \
        google-auth==1.6.2 \
        google-auth-oauthlib==0.2.0 \
        requests_oauthlib==1.0.0

RUN apt-get clean -y
RUN rm -rf /var/lib/apt/lists/*

ENV DEBIAN_FRONTEND newt
ENV PYTHONIOENCODING utf-8

# Copy data
COPY run.sh /
COPY *.py /

RUN chmod a+x /root/ascii2utf8.sh
RUN chmod a+x /run.sh

WORKDIR /share

ENTRYPOINT [ "/run.sh" ]
