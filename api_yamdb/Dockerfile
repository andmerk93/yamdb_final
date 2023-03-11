FROM python:3.7-slim

WORKDIR /app

COPY ./requirements.txt .

RUN pip3 install -r requirements.txt --no-cache-dir

# RUN python manage.py migrate

RUN python manage.py collectstatic --no-input

COPY ./ .

CMD ["gunicorn", "api_yamdb.wsgi:application", "--bind", "0:80"]