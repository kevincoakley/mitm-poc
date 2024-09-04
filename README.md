# ollama-middleware


## Run in debug mode

```bash
    export DEBUG=True
    python ./ollama_middleware.py
```

## Build the docker container

```bash
    docker build . --file Dockerfile --tag ollama-middleware
```

## Run the docker container

```bash
    docker compose up
```