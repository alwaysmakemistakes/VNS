1 Зарегистрировать пользователей

for i in $(seq 1 30); do
  curl -s -X POST http://localhost/users/register \
    -H "Content-Type: application/json" \
    -d '{"username": "user'$i'", "password": "pass'$i'"}'
done


2 Залогиниться и получить токен

TOKEN=$(curl -s -X POST http://localhost/users/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user1", "password":"pass1"}' | jq -r .token)
echo $TOKEN

3 Добавить товары в корзину

for i in $(seq 1 50); do
  curl -s -X POST http://localhost/cart \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"product_id": 2}'
done


4 Получить содержимое корзины

for i in $(seq 1 20); do
  curl -s -X GET http://localhost/cart \
    -H "Authorization: Bearer $TOKEN" | jq
done


5. Удалить товары из корзины

for i in $(seq 1 10); do
  curl -s -X DELETE http://localhost/cart/$i \
    -H "Authorization: Bearer $TOKEN" | jq
done




IP 

docker exec -it sad-nginx-1 getent hosts orders.local




Backup

1.

ls -lh ./pg_backup

2. 

docker exec -it postgres-master psql -U admin app_db

3.

DROP SCHEMA public CASCADE;
CREATE SCHEMA public;

4.

docker exec -i postgres-master psql -U admin app_db < ./pg_backup/backup_.sql

5. 

docker exec -it postgres-master psql -U admin app_db


6. 
SELECT * FROM users;
SELECT * FROM products;
SELECT * FROM orders;