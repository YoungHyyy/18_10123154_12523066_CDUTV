FROM nginx:1.27-alpine

COPY app/frontend/index.html /usr/share/nginx/html/index.html
COPY app/frontend/app.js /usr/share/nginx/html/app.js
COPY app/frontend/style.css /usr/share/nginx/html/style.css
COPY app/frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY app/frontend/health-status.sh /docker-entrypoint.d/05-health-status.sh
RUN chmod +x /docker-entrypoint.d/05-health-status.sh

EXPOSE 80
