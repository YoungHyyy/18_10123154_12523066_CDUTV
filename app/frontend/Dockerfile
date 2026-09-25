FROM nginx:1.27-alpine

COPY app/frontend/index.html /usr/share/nginx/html/index.html
COPY app/frontend/app.js /usr/share/nginx/html/app.js
COPY app/frontend/style.css /usr/share/nginx/html/style.css
COPY app/frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
