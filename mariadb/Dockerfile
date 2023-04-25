FROM mariadb:latest

COPY import.sql /docker-entrypoint-initdb.d/
RUN chmod -R 777 /docker-entrypoint-initdb.d/