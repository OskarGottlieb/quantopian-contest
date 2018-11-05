FROM python:3.7.1

RUN mkdir -p /srv/dash/
COPY . /srv/dash
WORKDIR /srv/dash
RUN pip install -r requirements.txt

RUN python data.py download
RUN python data.py aggregate

EXPOSE 8050
CMD ["python",  "app.py"]