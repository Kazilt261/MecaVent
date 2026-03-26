FROM ubuntu:24.04 AS builder

ARG DEBIAN_FRONTEND=noninteractive
ARG PYTHON_VERSION=3.14.0
ARG NODE_VERSION=25.0.0

RUN apt-get update && apt-get install -y --no-install-recommends \
	ca-certificates \
	curl \
	xz-utils \
	build-essential \
	pkg-config \
	libssl-dev \
	zlib1g-dev \
	libbz2-dev \
	libreadline-dev \
	libsqlite3-dev \
	libffi-dev \
	libncursesw5-dev \
	libgdbm-dev \
	liblzma-dev \
	tk-dev \
	uuid-dev \
	&& rm -rf /var/lib/apt/lists/*

# Install Node.js 25 from official tarball.
RUN curl -fsSL "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.xz" -o /tmp/node.tar.xz \
	&& mkdir -p /opt/node \
	&& tar -xJf /tmp/node.tar.xz -C /opt/node --strip-components=1 \
	&& rm -f /tmp/node.tar.xz

# Build and install Python 3.14.
RUN curl -fsSL "https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tar.xz" -o /tmp/python.tar.xz \
	&& tar -xJf /tmp/python.tar.xz -C /tmp \
	&& cd "/tmp/Python-${PYTHON_VERSION}" \
	&& ./configure --prefix=/opt/python3.14 --enable-optimizations --with-lto \
	&& make -j"$(nproc)" \
	&& make install \
	&& rm -rf "/tmp/Python-${PYTHON_VERSION}" /tmp/python.tar.xz

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

ENV PATH="/opt/python3.14/bin:/opt/node/bin:${PATH}"

WORKDIR /build

COPY backend ./backend
RUN cd /build/backend && uv sync --frozen --no-dev

COPY frontend ./frontend
RUN cd /build/frontend && npm ci && npm run build


FROM ubuntu:24.04 AS runtime

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
	ca-certificates \
	curl \
	bash \
	libssl3 \
	zlib1g \
	libbz2-1.0 \
	libreadline8 \
	libsqlite3-0 \
	libffi8 \
	libncursesw6 \
	libgdbm6 \
	liblzma5 \
	libatomic1 \
	libuuid1 \
	&& rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/python3.14 /opt/python3.14
COPY --from=builder /opt/node /opt/node

ENV PATH="/opt/python3.14/bin:/opt/node/bin:${PATH}"
ENV BACKEND_PORT=5000
ENV FRONTEND_PORT=5173

WORKDIR /app

COPY --from=builder /build/backend /app/backend
COPY --from=builder /build/frontend /app/frontend

EXPOSE 5000 5173

CMD ["bash", "-lc", "set -euo pipefail; trap 'kill -TERM ${BACK_PID:-0} ${FRONT_PID:-0} 2>/dev/null || true' INT TERM EXIT; cd /app/backend; ./.venv/bin/python manage.py migrate; ./.venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port ${BACKEND_PORT} & BACK_PID=$!; cd /app/frontend; npm run preview -- --host 0.0.0.0 --port ${FRONTEND_PORT} & FRONT_PID=$!; wait -n $BACK_PID $FRONT_PID"]