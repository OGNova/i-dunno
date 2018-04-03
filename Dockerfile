FROM python:3.6

ENV PYTHONUNBUFFERED 1
ENV ENV docker

RUN mkdir /opt/aetherya

ADD requirements.txt /opt/aetherya/
RUN python -m pip install -r /opt/aetherya/requirements.txt

ADD . /opt/aetherya/
WORKDIR /opt/aetherya

CMD ["python -m disco.cli --config config.yaml"]