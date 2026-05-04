FROM python:3.12-alpine

ENV RS_SURFACE_PROFILE=/etc/rs-surface/node.json
ENV RS_SURFACE_STATE=/var/lib/rs-surface
ENV RS_SURFACE_MOUNT=/mnt/topological-storage
ENV RS_SURFACE_HOST=0.0.0.0
ENV RS_SURFACE_PORT=8080

RUN adduser -D -H -u 988 surface \
    && mkdir -p /opt/rs-surface /etc/rs-surface /var/lib/rs-surface /var/log/rs-surface /run/rs-surface /mnt/topological-storage \
    && chown -R surface:surface /var/lib/rs-surface /var/log/rs-surface /run/rs-surface /mnt/topological-storage

COPY server.py /opt/rs-surface/server.py
COPY test_ws_client.py /opt/rs-surface/test_ws_client.py
COPY profiles/racknerd-surface.json /etc/rs-surface/node.json

USER surface
EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=3s --start-period=3s --retries=3 \
  CMD python /opt/rs-surface/test_ws_client.py --http-only --host 127.0.0.1 --port 8080

CMD ["python", "/opt/rs-surface/server.py"]
