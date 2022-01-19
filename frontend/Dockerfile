# develop stage
FROM node as develop-stage
WORKDIR /app
COPY ./quasar/package*.json ./
RUN npm install -g @quasar/cli
COPY ./quasar .

# build stage
FROM develop-stage as build-stage
RUN npm install
RUN quasar build

# production stage
FROM nginx:alpine as production-stage
COPY --from=build-stage /app/dist/spa /usr/share/nginx/html
COPY ./nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
