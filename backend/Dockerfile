FROM python:3.13-slim

WORKDIR /app
# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the application into the container.
COPY . /app

RUN chmod +x entrypoint.sh

# Install the application dependencies.
RUN uv sync --frozen --no-cache

# Run the application.
CMD ["./entrypoint.sh"]