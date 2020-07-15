FROM phusion/baseimage:0.11
MAINTAINER Christopher Krah <christopher.krah@fkie.fraunhofer.de>

# Configure proxy if needed
#ENV http_proxy <http_proxy>
#ENV https_proxy <https_proxy>

# install dependencies 
RUN apt-get update -y && apt-get install -y gcc cmake make wget screen gdb \
python automake git htop python3 build-essential python3-setuptools python3-dev \
python3-pip nginx

RUN pip3 install --upgrade pip
RUN pip3 install Flask flask-security flask-mongoengine bcrypt uwsgi python-dateutil email_validator


# create SSL certificate
RUN openssl req -subj '/CN=localhost' -x509 -newkey rsa:4096 -nodes -keyout /etc/nginx/conf.d/key.pem -out /etc/nginx/conf.d/cert.pem -days 365

# copy f3c source into container and install
WORKDIR /opt
RUN mkdir /opt/luckycat && mkdir /opt/luckycat/samples && mkdir /opt/luckycat/results
COPY . /opt/luckycat
COPY docker/frontend/start_frontend.sh /opt/luckycat/

# pull further dependencies
RUN wget https://github.com/chartjs/Chart.js/releases/download/v2.9.3/Chart.bundle.js -P /opt/luckycat/luckycat/frontend/static/
RUN wget https://raw.githubusercontent.com/mephux/hexdump.js/master/src/hexdump.js -P /opt/luckycat/luckycat/frontend/static/
RUN wget http://incaseofstairs.com/jsdiff/diff.js -P /opt/luckycat/luckycat/frontend/static/


EXPOSE 5000
CMD ["/bin/bash", "/opt/luckycat/start_frontend.sh"]
