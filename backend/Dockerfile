# Usa una versión estable a menos que necesites específicamente 3.14
FROM python:3.14-slim

# 1. Instalar uv de la forma más rápida y limpia (oficial)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 2. Configurar el entorno para instalar en el sistema del contenedor
ENV UV_PROJECT_ENVIRONMENT="/usr/local"
# Evita que uv intente descargar Python por su cuenta (usa el de la imagen base)
ENV UV_PYTHON_INSTALL_DIR="/usr/local"

WORKDIR /app

# 3. Aprovechar el caché de capas de Docker
# Copiamos solo los archivos de dependencias primero
COPY pyproject.toml uv.lock ./

# 4. Instalar dependencias usando montajes de caché
# Esto hace que 'uv' no tenga que descargar todo de nuevo si cambias el lockfile
RUN uv sync --locked

COPY . .