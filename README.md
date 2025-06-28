```
mermaid
graph TD
    subgraph Users_Service
        users1[users1 (Flask)]
        users2[users2 (Flask)]
    end

    subgraph Orders_Service
        orders1[orders1 (Flask)]
        orders2[orders2 (Flask)]
        order_worker[order-worker (Python Worker)]
    end

    subgraph Products_Service
        products1[products1 (Flask)]
        products2[products2 (Flask)]
    end

    subgraph Audit_Service
        audit_service[audit_service (Flask)]
    end

    subgraph PostgreSQL_Cluster
        monitor[(pg-monitor)]
        postgres_master[(postgres-master)]
        postgres_slave1[(postgres-slave1)]
        postgres_slave2[(postgres-slave2)]
    end

    subgraph RabbitMQ_Cluster
        rabbitmq1[(rabbitmq1)]
        rabbitmq2[(rabbitmq2)]
        rabbitmq3[(rabbitmq3)]
    end

    subgraph Frontend
        frontend1[frontend1 (Nginx + HTML/JS)]
        nginx[(Nginx Reverse Proxy)]
    end

    subgraph Observability
        prometheus[(Prometheus)]
        grafana[(Grafana)]
        postgres_exporter[(Postgres Exporter)]
    end

    subgraph DNS
        dnsmasq[(dnsmasq)]
    end

    subgraph BotRunners
        bot1[bot-runner1]
        bot2[bot-runner2]
        bot3[bot-runner3]
    end

    dnsmasq --> nginx

    frontend1 --> nginx

    nginx --> users1
    nginx --> users2
    nginx --> orders1
    nginx --> orders2
    nginx --> products1
    nginx --> products2

    users1 --> postgres_master
    users2 --> postgres_master
    users1 --> audit_service
    users2 --> audit_service

    orders1 --> postgres_master
    orders2 --> postgres_master

    products1 --> postgres_master
    products2 --> postgres_master

    orders1 -->|publish messages| rabbitmq1
    orders1 -->|publish messages| rabbitmq2
    orders1 -->|publish messages| rabbitmq3

    orders2 -->|publish messages| rabbitmq1
    orders2 -->|publish messages| rabbitmq2
    orders2 -->|publish messages| rabbitmq3

    order_worker -->|consume messages| rabbitmq1
    order_worker -->|consume messages| rabbitmq2
    order_worker -->|consume messages| rabbitmq3

    audit_service --> postgres_master

    postgres_exporter --> prometheus
    prometheus --> grafana

    bot1 --> nginx
    bot2 --> nginx
    bot3 --> nginx

    monitor --> postgres_master
    monitor --> postgres_slave1
    monitor --> postgres_slave2
```
