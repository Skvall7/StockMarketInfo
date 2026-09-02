# Используем официальный образ Python в качестве базового
FROM python:3.12-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Устанавливаем зависимости системы
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл зависимостей и устанавливаем Python-библиотеки
COPY requirements.txt /app/

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем исходный код проекта; логи исключены из build context через .dockerignore
COPY . /app/

RUN mkdir -p /app/var/logs && chmod -R 777 /app/var/logs


# Указываем переменную окружения для Python
ENV PYTHONUNBUFFERED=1

# Открываем порт, на котором будет работать приложение
EXPOSE 9000

# Логи приложения пишутся в /app/var/logs/smi.log
VOLUME ["/app/var/logs"]

# Команда для запуска приложения через uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]
