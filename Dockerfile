FROM python:3.10-slim
MAINTAINER Kevin Coakley <kcoakley@sdsc.edu>

ENV REMOTE_HOST=127.0.0.1
ENV REMOTE_PORT=11434
ENV DEBUG=""

RUN mkdir /ollama-middleware

COPY . /ollama-middleware
WORKDIR /ollama-middleware

RUN pip install -r requirements.txt

RUN groupadd -g 999 ollama && \
    useradd -r -u 999 -g ollama ollama

RUN chown -R ollama:ollama /ollama-middleware

USER ollama

EXPOSE 8080

CMD python ./ollama_middleware.py