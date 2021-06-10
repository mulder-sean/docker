LABEL description="Truncate files in /var/log/**/* because you should be streaming them and we don't need to retain on image."
COPY logs.conf /etc/logrotate.d/logs
RUN apt-get update && apt-get install -y logrotate && chmod 644 /etc/logrotate.d/logs
