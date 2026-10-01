import json
import socket
import threading
import time
import unittest

import server
import tasks


class TaskApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cls.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        cls.listener.bind(("127.0.0.1", 0))
        cls.listener.listen()
        cls.port = cls.listener.getsockname()[1]
        cls.stop = threading.Event()

        def serve():
            while not cls.stop.is_set():
                cls.listener.settimeout(0.1)
                try:
                    client, _ = cls.listener.accept()
                except socket.timeout:
                    continue
                except OSError:
                    break
                threading.Thread(target=server.handle_client, args=(client,), daemon=True).start()

        cls.thread = threading.Thread(target=serve, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.stop.set()
        cls.listener.close()
        cls.thread.join(timeout=1)

    def setUp(self):
        tasks.reset_tasks()

    def request(self, method, path, data=None):
        body = b"" if data is None else json.dumps(data).encode()
        request = (
            f"{method} {path} HTTP/1.1\r\nHost: test\r\n"
            f"Content-Length: {len(body)}\r\n\r\n"
        ).encode() + body
        with socket.create_connection(("127.0.0.1", self.port)) as client:
            client.sendall(request)
            reply = b""
            while chunk := client.recv(4096):
                reply += chunk
        head, body = reply.split(b"\r\n\r\n", 1)
        return int(head.split(b" ")[1]), json.loads(body) if body else None

    def create(self, title="Original", done=False):
        status, payload = self.request("POST", "/tasks", {"title": title, "done": done})
        self.assertEqual(status, 201)
        return payload["id"]

    def test_01_create_task(self):
        status, payload = self.request("POST", "/tasks", {"title": "Learn HTTP"})
        self.assertEqual((status, payload["title"], payload["done"]), (201, "Learn HTTP", False))

    def test_03_get_task(self):
        task_id = self.create()
        self.assertEqual(self.request("GET", f"/tasks/{task_id}")[0], 200)
        self.assertEqual(self.request("GET", "/tasks/999")[1]["code"], "task_not_found")
        self.assertEqual(self.request("GET", "/tasks/abc")[0], 400)

    def test_06_patch_done_and_empty(self):
        task_id = self.create()
        status, payload = self.request("PATCH", f"/tasks/{task_id}", {"done": True})
        self.assertEqual((status, payload["title"], payload["done"]), (200, "Original", True))
        self.assertEqual(self.request("PATCH", f"/tasks/{task_id}", {})[0], 200)

    def test_07_and_08_patch_validation(self):
        task_id = self.create()
        self.assertEqual(self.request("PATCH", f"/tasks/{task_id}", {"titel": "x"})[0], 422)
        self.assertEqual(self.request("PATCH", f"/tasks/{task_id}", {"title": None})[0], 422)
        self.assertEqual(self.request("PATCH", f"/tasks/{task_id}", {"done": 1})[0], 422)

    def test_09_put_replaces_all_fields(self):
        task_id = self.create(done=True)
        status, payload = self.request("PUT", f"/tasks/{task_id}", {"title": "Read lesson 15"})
        self.assertEqual((status, payload["title"], payload["done"]), (200, "Read lesson 15", False))

    def test_10_patch_list_is_405_but_missing_path_is_404(self):
        self.assertEqual(self.request("PATCH", "/tasks", {})[0], 405)
        self.assertEqual(self.request("GET", "/nothing-here")[0], 404)

    def test_11_and_13_delete(self):
        task_id = self.create()
        self.assertEqual(self.request("DELETE", f"/tasks/{task_id}"), (204, None))
        self.assertEqual(self.request("DELETE", f"/tasks/{task_id}")[0], 404)


if __name__ == "__main__":
    unittest.main(verbosity=2)
