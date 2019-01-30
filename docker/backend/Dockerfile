FROM arm32v7/ubuntu:latest
ENV DEBIAN_FRONTEND="noninteractive"
MAINTAINER Christopher Krah <krah@protonmail.com>

# install dependencies 
RUN apt-get update -y && apt-get install -y libffi-dev libffi6 gcc cmake make wget screen gdb htop mailutils \
automake build-essential git python3 python3-setuptools python3-yaml python3-dev python3-pip \
python3-pika

# install radamsa
WORKDIR /opt
RUN git clone https://gitlab.com/akihe/radamsa.git
WORKDIR /opt/radamsa
RUN make && make install

RUN pip3 install flask-mongoengine flask-security tabulate

# copy f3c source into container and install
WORKDIR /opt
RUN mkdir /opt/luckycat && mkdir /opt/luckycat/samples && mkdir /opt/luckycat/results && mkdir /opt/luckycat/results/crashes
COPY . /opt/luckycat/
COPY docker/backend/start_backend.sh /opt/luckycat/

CMD ["/bin/bash", "/opt/luckycat/start_backend.sh"]
