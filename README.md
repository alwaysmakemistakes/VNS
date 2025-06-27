# VNS

Шаблоны простых высоконагруженных систем (Docker)
                                  ┌─────────────┐
                                  │   Browser   │
                                  └─────┬───────┘
                                        │
                                        │ HTTP
                                        ▼
                                  ┌─────────────┐
                                  │    NGINX    │
                                  │ (LB & Cache)│
                                  └─────┬───────┘
                       ┌───────────────┼───────────────┐
                       │               │               │
            ┌──────────▼─────────┐ ┌───▼─────────┐ ┌───▼─────────┐
            │   Frontend #1      │ │ Frontend #2 │ │   CDN /    │
            │                    │ │             │ │  Static    │
            └──────────┬─────────┘ └─────────────┘ │  content   │
                       │                         └─────────────┘
                Proxies /users/ │ /orders/ │ /products/
                       │
 ┌───────────┬─────────┴─────────────┬──────────────┐
 │           │                       │              │
 ▼           ▼                       ▼              ▼
Users #1    Users #2             Orders #1       Orders #2
Service     Service              Service         Service
(port 5000) (port 5000)          (port 5000)     (port 5000)

(POST /users/login)           (POST /orders/checkout)
(POST /users/register)        (GET /orders)
(GET /users/me)               (GET /cart, POST /cart)

 ┌─────────────────────────────────────────────────────────┐
 │                        Products #1, #2                  │
 │                 (GET /products/)                        │
 └─────────────────────────────────────────────────────────┘

            ┌───────────────┬─────────────────────────────┐
            │               │                             │
         ┌──▼──┐         ┌──▼──┐                       ┌──▼──┐
         │ RabbitMQ     │ Postgres Master              │ Audit │
         │  Queue       │ + Slaves (pg_auto_failover)  │Service│
         └──────┘       └────────┬──────────────┘      └──────┘
                                   │
                                   │
                              pg_exporter
                                   │
                      ┌────────────▼─────────────┐
                      │       Prometheus         │
                      └────────────┬─────────────┘
                                   │
                              ┌────▼────┐
                              │ Grafana │
                              └─────────┘


