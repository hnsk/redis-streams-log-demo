FROM python:3.12-alpine
COPY ./requirements.txt /app/requirements.txt
WORKDIR /app
RUN apk add gcc g++ make libffi-dev openssl-dev
RUN pip install -r requirements.txt
COPY . /app
ENTRYPOINT [ "/usr/local/bin/uvicorn" ]
CMD [ "--host", "0.0.0.0", "streamsplitter:app" ]
