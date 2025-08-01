# FROM hub.cellosign.com/cellosign/fonts-scratch AS fonts
FROM python:3.13-alpine AS python-upgraded

RUN echo "adding fonts"
# COPY --from=fonts / /usr/share/fonts/cellosign

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Jerusalem
ENV PYTHONPATH="${PYTHONPATH}:/src"

RUN echo "adding office to apk"
RUN apk upgrade --no-cache
RUN set -xe; \
    apk add --update --no-cache tini;\
    apk add --update --no-cache su-exec curl bash; \
    apk add --update --no-cache openjdk11-jre-headless; \
    apk add --update --no-cache icu-libs icu-dev; \
    apk add --update --no-cache libreoffice; \
    apk add --update --no-cache ttf-freefont ttf-opensans font-ubuntu ttf-inconsolata ttf-liberation ttf-dejavu; \
    apk add --update --no-cache msttcorefonts-installer fontconfig; \
    apk add --update --no-cache libmagic; \
    update-ms-fonts; \
    fc-cache -f;


RUN cat /etc/os-release
RUN soffice --version

FROM python-upgraded AS builder
ADD requirements.txt .

RUN apk add --no-cache --virtual .build-deps build-base libffi-dev openssl-dev && \
    mkdir /wheels && pip wheel -w /wheels -r requirements.txt && \
    apk del .build-deps && \
    rm -rf /tmp/* /var/tmp/* /root/.cache

FROM python-upgraded AS main

WORKDIR /
EXPOSE 8000

COPY --from=builder /wheels /wheels

RUN set -xe; \
    pip install --no-cache-dir /wheels/* && \
    rm -rf /var/cache/apk/* /var/lib/apt/lists/* /tmp/* /var/tmp/* /root/.cache /wheels

COPY ./src ./src

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM main AS dev
COPY requirements.dev.txt /requirements.dev.txt
RUN pip install -r /requirements.dev.txt