FROM apache/zeppelin:0.11.2

USER root

COPY ../spark/jars /opt/spark/jars

COPY ../spark/requirements.txt /tmp/

RUN pip install -r /tmp/requirements.txt

USER zeppelin