from dataclasses import asdict, dataclass
import json


@dataclass
class Task:
    id: int
    title: str
    done: bool = False


TASKS = []
NEXT_ID = 1


def find(task_id):
    return next((task for task in TASKS if task.id == task_id), None)


def not_found(task_id):
    return 404, {"code": "task_not_found", "detail": f"Task {task_id} was not found"}


def check_new(data):
    if not isinstance(data, dict):
        return "body must be a JSON object"
    if "title" not in data:
        return "title is required"
    if not isinstance(data["title"], str):
        return "title must be a string"
    if "done" in data and type(data["done"]) is not bool:
        return "done must be a boolean"
    return None


def check_patch(data):
    if not isinstance(data, dict):
        return "body must be a JSON object"
    allowed_fields = {"title", "done"}
    for field in data:
        if field not in allowed_fields:
            return f"unknown field: {field}"
    if "title" in data and not isinstance(data["title"], str):
        return "title must be a string"
    if "done" in data and type(data["done"]) is not bool:
        return "done must be a boolean"
    return None


def list_tasks():
    return 200, [asdict(task) for task in TASKS]


def create_task(body):
    global NEXT_ID
    data = json.loads(body)
    error = check_new(data)
    if error:
        return 422, {"detail": error}

    task = Task(id=NEXT_ID, title=data["title"], done=data.get("done", False))
    NEXT_ID += 1
    TASKS.append(task)
    return 201, asdict(task)


def get_task(task_id):
    task_id = int(task_id)
    task = find(task_id)
    return not_found(task_id) if task is None else (200, asdict(task))


def delete_task(task_id):
    task_id = int(task_id)
    task = find(task_id)
    if task is None:
        return not_found(task_id)
    TASKS.remove(task)
    return 204, None


def replace_task(task_id, body):
    task_id = int(task_id)
    task = find(task_id)
    if task is None:
        return not_found(task_id)

    data = json.loads(body)
    error = check_new(data)
    if error:
        return 422, {"detail": error}
    task.title = data["title"]
    task.done = data.get("done", False)
    return 200, asdict(task)


def patch_task(task_id, body):
    task_id = int(task_id)
    task = find(task_id)
    if task is None:
        return not_found(task_id)

    data = json.loads(body)
    error = check_patch(data)
    if error:
        return 422, {"detail": error}
    if "title" in data:
        task.title = data["title"]
    if "done" in data:
        task.done = data["done"]
    return 200, asdict(task)


def reset_tasks():
    global NEXT_ID
    TASKS.clear()
    NEXT_ID = 1