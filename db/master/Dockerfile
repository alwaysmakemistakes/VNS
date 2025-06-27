FROM postgres:15

COPY ./master_pg_hba.conf /etc/postgresql/pg_hba.conf
COPY ./master_postgresql.conf /etc/postgresql/postgresql.conf

CMD ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf"]
