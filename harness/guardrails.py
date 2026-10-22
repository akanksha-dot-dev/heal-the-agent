"""GUARDRAILS: the model proposes, the harness disposes.

Model-written code is UNTRUSTED INPUT. Two layers here:
  1. static_check(): an AST allow-list (cheap, catches the obvious).
  2. run_sandboxed(): run the code in a separate Python process with a timeout
     and a tiny set of builtins, so a bad patch can't hang or crash the agent.

HONEST NOTE: this is a speed bump and a teaching device, NOT a security boundary.
Real isolation = a container / VM (that's one reason Colab is a good place to run this).
"""
import ast
import json
import subprocess
import sys

ALLOWED_IMPORTS = {"re", "json", "math", "datetime", "typing", "decimal"}
FORBIDDEN_NAMES = {"eval", "exec", "open", "compile", "__import__", "input",
                   "globals", "locals", "vars", "getattr", "setattr", "delattr"}


def static_check(code: str) -> list[str]:
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return [f"SyntaxError: {e}"]
    problems = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] not in ALLOWED_IMPORTS:
                    problems.append(f"import '{alias.name}' is not allowed")
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] not in ALLOWED_IMPORTS:
                problems.append(f"import from '{node.module}' is not allowed")
        elif isinstance(node, ast.Name) and (node.id in FORBIDDEN_NAMES or node.id.startswith("__")):
            problems.append(f"use of '{node.id}' is not allowed")
        elif isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            problems.append(f"access to '{node.attr}' is not allowed")
    if not any(isinstance(n, ast.FunctionDef) and n.name == "parse_weather" for n in tree.body):
        problems.append("code must define parse_weather(raw)")
    return problems


# This tiny script is what actually runs inside the child process.
_CHILD = r'''
import json, sys, traceback, builtins
job = json.load(sys.stdin)
def _fmt(e):
    tb = e.__traceback__.tb_next or e.__traceback__   # hide our own plumbing frame
    return "".join(traceback.format_exception(type(e), e, tb))
ALLOWED = set(job["allowed_imports"])
def _import(name, *a, **k):
    if name.split(".")[0] not in ALLOWED:
        raise ImportError(f"import of {name!r} is blocked")
    return __import__(name, *a, **k)
safe = {n: getattr(builtins, n) for n in (
    "float int str bool dict list tuple set len min max round abs sum sorted enumerate zip range "
    "isinstance any all print Exception ValueError KeyError TypeError IndexError AttributeError "
    "ArithmeticError ZeroDivisionError NotImplementedError ImportError").split()}
safe["__import__"] = _import
ns = {"__builtins__": safe}
out = []
try:
    exec(compile(job["code"], "<candidate>", "exec"), ns)
    fn = ns["parse_weather"]
except Exception as e:
    print(json.dumps({"load_error": _fmt(e)})); sys.exit(0)
for payload in job["payloads"]:
    try:
        out.append({"ok": True, "result": fn(payload)})
    except Exception as e:
        out.append({"ok": False, "traceback": _fmt(e)})
print(json.dumps({"results": out}))
'''


def run_sandboxed(code: str, payloads: list[dict], timeout: float = 5.0) -> dict:
    """Run `parse_weather` from `code` on each payload in a child process.

    Returns {"results": [{"ok": True, "result": ...} | {"ok": False, "traceback": ...}, ...]}
         or {"load_error": "..."}  or {"timeout": True}
    """
    job = json.dumps({"code": code, "payloads": payloads, "allowed_imports": sorted(ALLOWED_IMPORTS)})
    try:
        proc = subprocess.run([sys.executable, "-I", "-c", _CHILD], input=job,
                              capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"timeout": True}
    if proc.returncode != 0 or not proc.stdout.strip():
        return {"load_error": proc.stderr.strip() or "child process failed"}
    return json.loads(proc.stdout.strip().splitlines()[-1])
