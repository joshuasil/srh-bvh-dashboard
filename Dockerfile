FROM ubuntu


RUN apt-get update
RUN apt-get install -y python3 python3-pip
RUN yes yes | apt-get install apache2-dev

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

COPY ./ /srh-bvh-dashboard
WORKDIR /srh-bvh-dashboard/src

EXPOSE 8080

CMD gunicorn --bind 0.0.0.0:$PORT app:server