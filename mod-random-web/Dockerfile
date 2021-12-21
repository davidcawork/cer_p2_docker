FROM ubuntu:20.04
COPY /src /src
COPY /templates /templates
COPY main.py /
COPY install.sh /
COPY requirements.txt /
RUN apt-get update \
    && apt-get install -y python3-pip python3-dev 
RUN pip3 install -r /requirements.txt
RUN chmod +x /install.sh
ENTRYPOINT ["/bin/bash", "-c", "/install.sh"]