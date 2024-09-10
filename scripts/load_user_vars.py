import json
import os
from typing import Union
import yaml

# Logging helper function for GitHub Actions
def log_issue(message: str, level: str = "error", file: str = "", line: int = None, column: int = None):
    if level == "error":
        print(f"::error file={file},line={line},col={column}::{message}")
    elif level == "warning":
        print(f"::warning file={file},line={line},col={column}::{message}")
    else:
        print(f"::debug::{message}")

# Set GitHub Actions environment variable
def set_variable(key: str, value: str, is_output: bool = False):
    if is_output:
        # Set as an output variable
        print(f"::set-output name={key}::{value}")
    else:
        # Set as an environment variable
        print(f"{key}={value}", file=open(os.getenv('GITHUB_ENV'), 'a'))

def walk(directory: Union[str, os.PathLike[str]], keys):
    for entry in os.scandir(directory):
        if entry.is_file():
            yield entry.path
        else:
            key, value = entry.name.split("=")
            if keys[key].lower() == value.lower():
                yield from walk(entry, keys)

def load_user_variables(path: str, keys: str):
    keys = json.loads(keys)

    files = list(walk(path, keys))
    files = sorted(files, key=lambda p: len(p.split("/")))

    variables = {}

    for file in files:
        with open(file, "r", encoding="utf-8") as stream:
            try:
                stream_yaml = yaml.safe_load(stream)
                if isinstance(stream_yaml, dict):
                    variables.update(stream_yaml)
                elif stream_yaml is None:
                    continue
                else:
                    log_issue(f"Expected a dictionary, got {type(stream_yaml).__name__}", level="error", file=file)
                    exit(1)
            except yaml.MarkedYAMLError as exc:
                if (
                    exc.context is not None
                    and exc.problem_mark is not None
                    and exc.problem is not None
                ):
                    log_issue(
                        exc.context + ": " + exc.problem,
                        level="error",
                        file=exc.problem_mark.name,
                        line=exc.problem_mark.line + 1,
                        column=exc.problem_mark.column + 1,
                    )
                exit(1)
            except yaml.YAMLError as exc:
                log_issue(str(exc), level="error")
                exit(1)

    # Output the variables
    print(variables)

    for key, value in variables.items():
        if isinstance(value, bool):
            value = str(value).lower()
        set_variable(key, value, is_output=True)
