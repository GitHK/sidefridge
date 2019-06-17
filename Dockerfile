FROM python:3.7.3-alpine

RUN apk update && apk add curl bash

# Add kubectl to container
RUN curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl
RUN chmod +x ./kubectl
RUN mv ./kubectl /usr/local/bin
RUN mkdir -p /scripts

COPY sidefridge /app/sidefridge
COPY setup.py /app

WORKDIR /app

RUN pip install -e .

# start crond with log level 8 in foreground, output to stderr
CMD ["sh", "-c", "fridge -i && crond -f -d 8"]