# Stage 1: Install dependencies
FROM node:18 as deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install

# Stage 2: Development (used by docker-compose)
FROM deps as development
# The command will be provided by docker-compose

# Stage 3: Build the static files for production
FROM deps as builder
COPY . .
RUN npm run build

# Stage 4: Production server (e.g., using nginx)
FROM nginx:alpine as production
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
