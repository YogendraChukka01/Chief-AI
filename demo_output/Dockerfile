FROM node:20-alpine AS frontend
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM python:3.12-slim AS backend
WORKDIR /app
COPY backend/ .
RUN pip install fastapi uvicorn

FROM python:3.12-slim
COPY --from=frontend /app/dist /app/static
COPY --from=backend /app /app
WORKDIR /app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
