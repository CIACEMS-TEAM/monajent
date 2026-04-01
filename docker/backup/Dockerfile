FROM postgres:16-alpine

RUN apk add --no-cache bash

COPY backup.sh /usr/local/bin/backup.sh
RUN chmod +x /usr/local/bin/backup.sh

RUN mkdir -p /backups

# Cron : backup toutes les 6 heures
RUN echo "0 */6 * * * /usr/local/bin/backup.sh >> /var/log/backup.log 2>&1" > /etc/crontabs/root

CMD ["crond", "-f", "-l", "2"]
