# Build stage
FROM python:3.13-alpine AS builder

# Install poetry
RUN pip install poetry

# Set working directory
WORKDIR /build

# Copy only dependencies files first
COPY pyproject.toml poetry.lock* ./

# Copy the rest of the application
COPY . .

# Build wheel
RUN poetry build --format wheel

# Runtime stage
FROM python:3.13-alpine

# Install SQLite
RUN apk add --no-cache sqlite

# Set working directory
WORKDIR /app

# Copy wheel from builder stage
COPY --from=builder /build/dist/*.whl .

# Install the wheel (no
RUN pip install *.whl

# Change the working directory
WORKDIR /data

# Declare /data directory as a volume (it will be used to store the SQLite database)
VOLUME /data

# Run the application
CMD ["prospero"]