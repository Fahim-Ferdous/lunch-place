# Running

## Without Docker

```sh
virtualenv .venv && source .venv/bin/activate && pip install -r requirements.txt
uvicorn main:app
```

## Using Docker

```sh
docker buildx b -t bongo_app .
docker run -p 8000:8000 bongo_app:latest
```

# Testing

To test locally, you can just run `pytest`, but you need some more dependencies.
Run `pip install -r requrements-dev.txt` to install them.

If you want to run the tests inside docker, then run the following,

```sh
docker buildx b -t bongo_app.test -f Dockerfile.test .
docker run bongo_app.test:latest
```

# TODO

- Logging
- Logout
- Ensure restaurant can't win 3 consecutive days.
- docker compose
- dockerize celery worker
