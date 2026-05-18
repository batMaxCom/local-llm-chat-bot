# Запуск
```
make dev            # запустить всё (2 процесса)
make dev-backend    # только backend на :8000
make dev-frontend   # только frontend на :5173
make build          # собрать фронтенд
make install        # uv sync + npm install
make clean          # удалить dist, node_modules, __pycache__
```