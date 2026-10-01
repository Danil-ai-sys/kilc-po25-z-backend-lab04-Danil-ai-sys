import tasks


ROUTES = {
    ("GET", "/tasks"): tasks.list_tasks,
    ("POST", "/tasks"): tasks.create_task,
    ("GET", "/tasks/{task_id}"): tasks.get_task,
    ("DELETE", "/tasks/{task_id}"): tasks.delete_task,
    ("PUT", "/tasks/{task_id}"): tasks.replace_task,
    ("PATCH", "/tasks/{task_id}"): tasks.patch_task,
}


def _match_path(pattern, path):
    pattern_parts = pattern.strip("/").split("/")
    path_parts = path.strip("/").split("/")
    if len(pattern_parts) != len(path_parts):
        return None

    parameters = {}
    for expected, actual in zip(pattern_parts, path_parts):
        if expected.startswith("{") and expected.endswith("}"):
            parameters[expected[1:-1]] = actual
        elif expected != actual:
            return None
    return parameters


def find_route(method, path):
    for (route_method, pattern), handler in ROUTES.items():
        parameters = _match_path(pattern, path)
        if route_method == method and parameters is not None:
            return handler, parameters
    return None


def path_exists(path):
    return any(_match_path(pattern, path) is not None for _, pattern in ROUTES)
