FROM node:16-alpine

COPY scripts/entrypoint.sh /usr/local/bin/entrypoint
RUN mkdir -p /build && \
    chmod +x /usr/local/bin/entrypoint

ENTRYPOINT ["/usr/local/bin/entrypoint"]
