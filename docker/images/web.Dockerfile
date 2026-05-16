# dataplat 前端镜像（多阶段：node 构建 → nginx 托管；占位骨架）
FROM node:20-slim AS build

WORKDIR /app

RUN npm install -g pnpm@9

COPY package.json pnpm-workspace.yaml pnpm-lock.yaml* ./
COPY apps/web ./apps/web
COPY packages/api-types ./packages/api-types

RUN pnpm install --frozen-lockfile || pnpm install

RUN pnpm --filter web build

FROM nginx:alpine

COPY --from=build /app/apps/web/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
