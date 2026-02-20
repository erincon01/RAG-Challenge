FROM node:22-alpine AS base

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# Use built-in non-root user (node:22-alpine includes user 'node' with UID 1000)
RUN chown -R node:node /app

# Development stage
FROM base AS development
USER node
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# Production build stage
FROM base AS production
ARG VITE_API_BASE_URL=/api/v1
ARG VITE_BACKEND_ORIGIN=http://backend:8000
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_BACKEND_ORIGIN=${VITE_BACKEND_ORIGIN}
RUN npm run build
USER node
EXPOSE 5173
CMD ["npm", "run", "serve"]
