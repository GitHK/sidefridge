FROM python:3.7.3-alpine

RUN apk update && apk add curl bash

# Add kubectl to container
RUN curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl
RUN chmod +x ./kubectl
RUN mv ./kubectl /usr/local/bin

# Create directory structure
RUN mkdir -p /scripts/install_dependencies
RUN mkdir -p /scripts/backups
RUN mkdir -p /scripts/before_backups
RUN mkdir -p /scripts/after_backups
RUN mkdir -p /scripts/on_error

# Path where to mount secrets
RUN mkdir -p /secrets

COPY sidefridge /app/sidefridge
COPY setup.py /app
COPY start.sh /app

WORKDIR /app

RUN pip install -e .

# start crond with log level 8 in foreground, output to stderr
CMD ["./start.sh"]