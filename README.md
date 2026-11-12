# Steamgrader

## Запуск на Windows

Запустите `start.cmd` двойным щелчком. Сайт откроется по адресу
`http://localhost:3000`. Нужен Node.js, а для первой установки зависимостей
фронтенда понадобится Yarn Classic.

Для запуска API нужны Python и работающая MongoDB. Создайте `backend/.env`
со следующими переменными:

```dotenv
MONGO_URL=mongodb://127.0.0.1:27017
DB_NAME=steamgrader
JWT_SECRET=
```

Задайте `JWT_SECRET` случайным значением, которое можно получить командой
`python -c "import secrets; print(secrets.token_urlsafe(32))"`.
При необходимости укажите `STEAM_API_KEY` для загрузки ника и аватара из Steam.
После настройки запустите `start.cmd`. API откроется в отдельном окне консоли.
