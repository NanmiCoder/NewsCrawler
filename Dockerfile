# ================================
# Multi-stage Dockerfile for News Extractor Collection
# Builds: Backend API + MCP Server + Frontend
# ================================

# --------------------------------
# Stage 1: Python Base with uv
# --------------------------------
FROM python:3.10-slim AS python-base

# Install uv package manager
RUN pip install --no-cache-dir uv

# Set working directory
WORKDIR /app

# Copy workspace configuration
COPY pyproject.toml uv.lock README.md ./

# Copy all workspace members
COPY news_extractor_core/ ./news_extractor_core/
COPY news_extractor_backend/ ./news_extractor_backend/
COPY news_extractor_mcp/ ./news_extractor_mcp/
COPY news_crawler/ ./news_crawler/

# Install all Python dependencies (syncs workspace)
RUN uv sync --frozen --no-dev

# --------------------------------
# Stage 2: Frontend Builder (Node.js)
# --------------------------------
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy frontend package files
COPY news-extractor-ui/frontend/package.json news-extractor-ui/frontend/package-lock.json* ./

# Install dependencies (use npm install if no lockfile, npm ci if lockfile exists)
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# Copy frontend source
COPY news-extractor-ui/frontend/ ./

# Build for production (outputs to dist/)
RUN npm run build

# --------------------------------
# Stage 3: Backend Runtime
# --------------------------------
FROM python-base AS backend

# Expose backend port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

# Default command
CMD ["uv", "run", "news-extractor-backend", "--host", "0.0.0.0", "--port", "8000"]

# --------------------------------
# Stage 4: MCP Server Runtime
# --------------------------------
FROM python-base AS mcp

# Expose MCP port
EXPOSE 8765

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8765/health')" || exit 1

# Default command
CMD ["uv", "run", "news-extractor-mcp", "--host", "0.0.0.0", "--port", "8765"]

# --------------------------------
# Stage 5: Frontend with Nginx
# --------------------------------
FROM nginx:alpine AS frontend

# Copy built frontend from builder
COPY --from=frontend-builder /app/frontend/dist /usr/share/nginx/html

# Copy custom nginx config
COPY <<EOF /etc/nginx/conf.d/default.conf
server {
    listen 80;
    server_name localhost;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Frontend static files
    location / {
        root /usr/share/nginx/html;
        try_files \$uri \$uri/ /index.html;
    }

    # Proxy API requests to backend
    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Expose frontend port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://127.0.0.1/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
