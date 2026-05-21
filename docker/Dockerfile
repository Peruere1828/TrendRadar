FROM python:3.12-slim-bookworm

WORKDIR /app

# Proxy support — pass via build args when behind a proxy
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY=localhost,127.0.0.1

# Test proxy connectivity; if unreachable, clear proxy settings
# Writes proxy env vars to /tmp/proxy_env for subsequent RUNs to source
# Does NOT bake proxy into final image via ENV
RUN if [ -n "$HTTP_PROXY" ] && \
      python3 -c "import socket,urllib.parse; p=urllib.parse.urlparse('$HTTP_PROXY'); s=socket.create_connection((p.hostname,p.port),timeout=5); s.close()" 2>/dev/null; then \
      echo "export HTTP_PROXY='$HTTP_PROXY' HTTPS_PROXY='$HTTPS_PROXY' NO_PROXY='$NO_PROXY'" > /tmp/proxy_env; \
      echo "Proxy reachable: $HTTP_PROXY"; \
    else \
      echo "unset HTTP_PROXY HTTPS_PROXY NO_PROXY http_proxy https_proxy no_proxy" > /tmp/proxy_env; \
      if [ -n "$HTTP_PROXY" ]; then \
        echo "WARNING: Proxy $HTTP_PROXY is unreachable, proceeding without proxy"; \
      else \
        echo "No proxy configured"; \
      fi; \
    fi

# Latest releases available at https://github.com/aptible/supercronic/releases
ARG TARGETARCH
ENV SUPERCRONIC_VERSION=v0.2.39

RUN set -ex && \
    . /tmp/proxy_env && \
    apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    case ${TARGETARCH} in \
    amd64) \
    export SUPERCRONIC_URL=https://github.com/aptible/supercronic/releases/download/${SUPERCRONIC_VERSION}/supercronic-linux-amd64; \
    export SUPERCRONIC_SHA1SUM=c98bbf82c5f648aaac8708c182cc83046fe48423; \
    export SUPERCRONIC=supercronic-linux-amd64; \
    ;; \
    arm64) \
    export SUPERCRONIC_URL=https://github.com/aptible/supercronic/releases/download/${SUPERCRONIC_VERSION}/supercronic-linux-arm64; \
    export SUPERCRONIC_SHA1SUM=5ef4ccc3d43f12d0f6c3763758bc37cc4e5af76e; \
    export SUPERCRONIC=supercronic-linux-arm64; \
    ;; \
    *) \
    echo "Unsupported architecture: ${TARGETARCH}"; \
    exit 1; \
    ;; \
    esac && \
    echo "Downloading supercronic for ${TARGETARCH} from ${SUPERCRONIC_URL}" && \
    # Retry mechanism: up to 3 times, 30s timeout each
    for i in 1 2 3; do \
        echo "Download attempt $i/3"; \
        if curl -fsSL --connect-timeout 30 --max-time 60 -o "$SUPERCRONIC" "$SUPERCRONIC_URL"; then \
            echo "Download successful"; \
            break; \
        else \
            echo "Download attempt $i failed"; \
            if [ $i -eq 3 ]; then \
                echo "All download attempts failed"; \
                exit 1; \
            fi; \
            sleep 2; \
        fi; \
    done && \
    echo "${SUPERCRONIC_SHA1SUM}  ${SUPERCRONIC}" | sha1sum -c - && \
    chmod +x "$SUPERCRONIC" && \
    mv "$SUPERCRONIC" "/usr/local/bin/${SUPERCRONIC}" && \
    ln -s "/usr/local/bin/${SUPERCRONIC}" /usr/local/bin/supercronic && \
    supercronic -version && \
    apt-get remove -y curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy uv binary from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install dependencies (leverage Docker layer caching)
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    . /tmp/proxy_env && \
    uv sync --locked --no-install-project --no-dev

# Copy project code and install the project itself
COPY docker/manage.py .
COPY trendradar/ ./trendradar/
RUN --mount=type=cache,target=/root/.cache/uv \
    . /tmp/proxy_env && \
    uv sync --locked --no-dev

ENV PATH="/app/.venv/bin:$PATH"

# Copy entrypoint.sh and force LF line endings
COPY docker/entrypoint.sh /entrypoint.sh.tmp
RUN sed -i 's/\r$//' /entrypoint.sh.tmp && \
    mv /entrypoint.sh.tmp /entrypoint.sh && \
    chmod +x /entrypoint.sh && \
    chmod +x manage.py && \
    mkdir -p /app/config /app/output

ENV PYTHONUNBUFFERED=1 \
    CONFIG_PATH=/app/config/config.yaml \
    FREQUENCY_WORDS_PATH=/app/config/frequency_words.txt

ENTRYPOINT ["/entrypoint.sh"]
