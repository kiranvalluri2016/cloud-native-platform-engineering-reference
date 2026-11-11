FROM python:3.12-alpine

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src

WORKDIR /app

RUN addgroup -S -g 10001 app && adduser -S -D -H -u 10001 -G app app

COPY --chown=10001:10001 src ./src

USER 10001:10001

EXPOSE 8080

CMD ["python", "-m", "cloud_native_reference.app"]
