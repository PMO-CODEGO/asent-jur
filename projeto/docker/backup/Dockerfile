FROM mysql:8

RUN microdnf install -y cronie && microdnf clean all

COPY backup.sh /usr/local/bin/backup.sh
RUN chmod +x /usr/local/bin/backup.sh

# Roda backup todo dia às 02:00
RUN echo "0 2 * * * root /usr/local/bin/backup.sh >> /var/log/backup.log 2>&1" > /etc/cron.d/db-backup \
    && chmod 0644 /etc/cron.d/db-backup

CMD ["crond", "-n"]
