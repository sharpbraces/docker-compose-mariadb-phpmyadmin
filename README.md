# docker-compose-mariadb-phpmyadmin
Dev environment for MariaDB and PhpMyAdmin.

If you have Docker Desktop installed just download the repository and in the newly created folder type:

```
docker-compose build
```

and

```
docker-compose up -d
```

In your browser just go to http://localhost:5050 and PhpMyAdmin should appears there.
If you want to import some data then place your import.sql file inside the mariadb folder before building.