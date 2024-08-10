# syntax=docker/dockerfile:1
FROM python:3.12-alpine3.19 as python-base
# Alpine pinned to 3.19 since I've experience issues with 3.20 in a separate project
# If you encounter any issues at all with Alpine, switch to Python:3.12-slim-bookworm

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
