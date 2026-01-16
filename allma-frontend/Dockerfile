# =============================================================================
# Allma AI Studio - Frontend Dockerfile
# Multi-stage build: Node.js build -> Nginx serve
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Dependencies - Install and cache node_modules
# -----------------------------------------------------------------------------
FROM node:25-alpine AS deps

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci --only=production=false

# -----------------------------------------------------------------------------
# Stage 2: Builder - Build the application
# -----------------------------------------------------------------------------
FROM node:25-alpine AS builder

WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy source code
COPY . .

# Build arguments for environment configuration
ARG VITE_API_URL=http://localhost:8000
ARG VITE_APP_NAME="Allma AI Studio"
ARG VITE_APP_VERSION="1.0.0"

# Set environment variables for build
ENV VITE_API_URL=${VITE_API_URL} \
    VITE_APP_NAME=${VITE_APP_NAME} \
    VITE_APP_VERSION=${VITE_APP_VERSION}

# Build the application
RUN npm run build

# -----------------------------------------------------------------------------
# Stage 3: Production - Nginx server
# -----------------------------------------------------------------------------
FROM nginx:1.25-alpine AS production

# Labels for container metadata
LABEL org.opencontainers.image.title="Allma AI Studio Frontend" \
      org.opencontainers.image.description="React frontend for Allma AI Studio" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.vendor="Allma Studio"

# Install curl for healthcheck
RUN apk add --no-cache curl

# Remove default nginx config
RUN rm -rf /etc/nginx/conf.d/default.conf

# Copy custom nginx configuration
COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY nginx/default.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Create non-root user
RUN addgroup -g 1000 -S allma && \
    adduser -u 1000 -S allma -G allma && \
    chown -R allma:allma /var/cache/nginx && \
    chown -R allma:allma /var/log/nginx && \
    chown -R allma:allma /etc/nginx/conf.d && \
    touch /var/run/nginx.pid && \
    chown -R allma:allma /var/run/nginx.pid && \
    chown -R allma:allma /usr/share/nginx/html

# Switch to non-root user
USER allma

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
