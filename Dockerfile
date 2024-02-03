ARG PYTHON_VERSION=3.11-slim-bullseye

FROM python:${PYTHON_VERSION}

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir -p /code

WORKDIR /code

RUN apt-get update && apt-get install -y \
    libpq-dev postgresql-client gcc git curl \
    binutils libproj-dev gdal-bin \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g yarn

RUN mkdir -p /code/web
COPY ./web/package.json /code/web/package.json
COPY ./web/yarn.lock /code/web/yarn.lock
RUN cd /code/web && ls -lah && yarn install

COPY requirements.txt /tmp/requirements.txt
RUN set -ex && \
    pip install --upgrade pip && \
    pip install psycopg2 && \
    pip install -r /tmp/requirements.txt && \
    rm -rf /root/.cache/
COPY . /code

RUN cd /code/web && yarn build

ENV SECRET_KEY "OE3iYRlyBiJ0texNe5lqbvqRrxg1kN8Db540QaFMe9zrhVcIGu"
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--bind", ":8000", "--workers", "2", "--access-logfile", "-", "charging.wsgi"]
