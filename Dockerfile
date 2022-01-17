# develop stage
FROM node as develop-stage
WORKDIR /app
COPY frontend/package*.json ./
RUN npm install -g @quasar/cli
COPY ./frontend .

# build stage
FROM develop-stage as build-stage
RUN npm install
RUN quasar build

FROM python:3.10.1
COPY ./requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt
COPY . /app
COPY --from=build-stage /app/dist/spa /app/static
ENTRYPOINT [ "/usr/local/bin/uvicorn" ]
CMD [ "--host", "0.0.0.0", "websocket:app" ]
