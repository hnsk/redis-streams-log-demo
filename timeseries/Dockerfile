FROM python:3.10.2-alpine
COPY ./requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt
COPY . /app
ENTRYPOINT [ "/usr/local/bin/uvicorn" ]
CMD [ "--host", "0.0.0.0", "timeseries:app" ]
