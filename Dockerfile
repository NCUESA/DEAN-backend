FROM python:3 AS DEANbackend

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN alembic upgrade head

EXPOSE 6600
CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "6600"]