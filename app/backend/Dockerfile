FROM node:22-alpine

WORKDIR /app

COPY app/backend/package*.json ./
RUN npm install --omit=dev

COPY app/backend/src ./src
COPY ai-models/models /app/models

ENV PORT=8000
ENV SCHEMA_PATH=/app/models/schema.json
EXPOSE 8000

CMD ["node", "src/server.js"]
