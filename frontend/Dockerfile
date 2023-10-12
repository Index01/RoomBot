FROM node:16-alpine

ENV REACT_APP_API_ENDPOINT=http://localhost:8080

COPY scripts/entrypoint.sh /usr/local/bin/entrypoint
RUN mkdir -p /build && \
    chmod +x /usr/local/bin/entrypoint

ENTRYPOINT ["/usr/local/bin/entrypoint"]
