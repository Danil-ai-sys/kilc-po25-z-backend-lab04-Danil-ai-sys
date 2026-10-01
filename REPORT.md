# Report

## Read-before-write answers

1. **Where does the server learn how long the body is?**  In `server.py`,
   `handle_client()` reads the lower-case `content-length` header and converts
   it to an integer before extending the bytes already received.

2. **What happens to broken JSON?**  `tasks.py`, `create_task()` raises
   `json.JSONDecodeError` at `json.loads(body)`; `server.py`, `handle_client()`
   catches it through `except (UnicodeDecodeError, ValueError)` and answers 400.

3. **Why does `create_task` return a pair?**  `tasks.py`, `create_task()`
   returns `(status, payload)` so `server.py`, `handle_client()` can write the
   HTTP status separately from the JSON body.  This also lets DELETE return
   `(204, None)` without a body.

## Deliberate failure checks

1. Undoing only the PUT/PATCH body-reading change can appear to work because
   `parsing.py`, `read_request()` often gets both headers and the small body in
   its first `recv(1024)`.  It fails when the body arrives later or is larger.

2. `POST /tasks` with `{"title": "x"}` returns **201 Created**.  The request
   is valid, so no exception is produced; `tasks.py`, `create_task()` creates
   the task.  (A malformed body such as `{"title":` returns 400 via the
   `ValueError` handler described above.)

3. A body shorter than `Content-Length` blocks in `server.py`,
   `handle_client()` at `client.recv(1024)` in the body-length loop.  Its
   five-second socket timeout is caught by the `except socket.timeout` block,
   which sends **408 Request Timeout**.

4. `PATCH /tasks/1` with `{"done": 1}` returns **422 Unprocessable Content**.
   `tasks.py`, `check_patch()` uses `type(value) is bool`, so the integer `1`
   is not accepted as `true`.
