FROM nginx:1.29.0

COPY ./docker/nginx/nginx.conf /etc/nginx/nginx.conf

RUN chown -R nginx:nginx /etc/nginx/

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]