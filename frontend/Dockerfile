# Frontend Dockerfile
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* .npmrc ./
# Use npm install (not npm ci) so platform-specific optional deps
# (@esbuild/*, @next/swc-linux-*, lightningcss-*) are resolved for this
# Linux build even when the lockfile was generated on another OS.
RUN npm install --no-audit --no-fund

FROM node:20-alpine AS builder
WORKDIR /app
# next.config.mjs resolves rewrites() at BUILD time, so BACKEND_URL must be
# available here (not just at runtime), otherwise the image bakes in the
# 'http://localhost:8000' fallback and the containerized frontend cannot
# reach the backend (ECONNREFUSED 127.0.0.1:8000 -> login 500).
ARG BACKEND_URL=http://backend:8000
ENV BACKEND_URL=$BACKEND_URL
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
ENV PORT=3000
CMD ["node", "server.js"]
