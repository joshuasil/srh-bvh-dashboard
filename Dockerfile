FROM ubuntu


RUN apt-get update
RUN apt-get install -y python3 python3-pip
RUN apt-get install apache2-dev

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

COPY ./ /srh-bvh-dashboard
WORKDIR /srh-bvh-dashboard/src

CMD gunicorn --bind 0.0.0.0:80 --workers=4 wsgi