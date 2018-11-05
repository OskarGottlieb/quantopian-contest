FROM python:3.7.1

RUN mkdir -p /srv/dash/
COPY requirements.txt /srv/dash
RUN pip install -r /srv/dash/requirements.txt

COPY . /srv/dash
WORKDIR /srv/dash

RUN python data.py download
RUN python data.py aggregate

EXPOSE 8050
CMD ["gunicorn",  "-b", "0.0.0.0:8050", "app:server"]