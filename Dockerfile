# syntax=docker/dockerfile:1
FROM python:3.12-alpine3.19 as python-base

# Grab security updates
RUN apk update && apk update --no-cache && apk cache clean

FROM python-base as demolition-checker

# Install dependencies
COPY /requirements.txt ./
RUN --mount=type=cache,target=/root/.cache \
    pip install -r requirements.txt

# Copy code 
RUN mkdir /demolition-checker
WORKDIR /demolition-checker
COPY ./main.py .

# Run the spider
ENTRYPOINT ["scrapy", "runspider", "main.py"]
