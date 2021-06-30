FROM node:14-slim as builder
ARG REACT_APP_API_URL
ENV REACT_APP_API_URL=$REACT_APP_API_URL


RUN mkdir -p /src/app/
COPY ./frontend/package.json /src/app/
WORKDIR /src/app

COPY ./frontend /src/app
RUN npm install
RUN yarn build

FROM nginx:1.15-alpine
MAINTAINER Azamat Tokhtaev

RUN mkdir -p /var/www/frontend

COPY --from=builder /src/app/build /var/www/frontend/

COPY ./docker-files/nginx/casa.nginx /etc/nginx/nginx.conf
ADD ./docker-files/nginx/start.sh /start.sh
RUN sed -i 's/\r//' /start.sh && \
    chmod +x /start.sh



RUN mkdir -p /var/log/nginx
CMD ["/start.sh"]
