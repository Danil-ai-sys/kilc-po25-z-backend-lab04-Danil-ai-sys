# Task API

Small dependency-free HTTP server implementing the exercise's `GET`, `POST`,
`PUT`, `PATCH`, and `DELETE` task endpoints.

## Run

From this directory, start the server with a Python 3 interpreter:

```text
python server.py
```

It listens on `http://127.0.0.1:8080` and retains tasks in memory until it is
stopped.  Run the integration checks with:

```text
python -m unittest -v
```

`REPORT.md` contains the requested answers and observations from the deliberate
failure cases.
