FROM apache/spark:3.5.4

USER root

COPY requirements.txt /tmp/
COPY jars/ /opt/spark/jars

RUN pip install --no-cache-dir -r /tmp/requirements.txt

USER spark