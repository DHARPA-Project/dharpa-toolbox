FROM debian:stable

RUN \
   apt update -y && \
   apt install -y wget git

COPY dharpa-toolbox /usr/bin/dharpa-toolbox

RUN \
   chmod +x /usr/bin/dharpa-toolbox
