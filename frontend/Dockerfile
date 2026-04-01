# ── Stage 1 : Dépendances ────────────────────────────────────
FROM node:22-alpine AS deps

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --ignore-scripts

# ── Stage 2 : Build ─────────────────────────────────────────
FROM node:22-alpine AS build

WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

ARG VITE_API_BASE_URL
ARG VITE_PAYSTACK_PUBLIC_KEY

ENV VITE_API_BASE_URL=$VITE_API_BASE_URL \
    VITE_PAYSTACK_PUBLIC_KEY=$VITE_PAYSTACK_PUBLIC_KEY

RUN npm run build-only

# ── Stage 3 : Runtime Nginx ─────────────────────────────────
FROM nginx:1.27-alpine

RUN rm -rf /usr/share/nginx/html/*

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

RUN addgroup -g 1001 -S app && adduser -S -u 1001 -G app app && \
    chown -R app:app /var/cache/nginx /var/log/nginx && \
    touch /var/run/nginx.pid && chown app:app /var/run/nginx.pid

USER app

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
