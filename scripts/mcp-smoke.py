#!/usr/bin/env python3
"""Minimal stdio MCP client to smoke-test the git MCP server.
Spawns `uvx mcp-server-git --repository <repo>` exactly as the orchestrator
config does, performs the initialize handshake, lists tools, and calls
git_status, git_log, and git_diff. Prints a compact PASS/FAIL per step.
"""
import json
import subprocess
import sys

REPO = "/Users/sharunikaass/Documents/kiro-proj"
CMD = ["uvx", "mcp-server-git", "--repository", REPO]

proc = subprocess.Popen(
    CMD, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    text=True, bufsize=1,
)

_id = 0
def send(method, params=None, is_notification=False):
    global _id
    msg = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        msg["params"] = params
    if not is_notification:
        _id += 1
        msg["id"] = _id
    proc.stdin.write(json.dumps(msg) + "\n")
    proc.stdin.flush()

def read_until_id(target_id, limit=200):
    for _ in range(limit):
        line = proc.stdout.readline()
        if not line:
            return None
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("id") == target_id:
            return obj
    return None

results = []
try:
    send("initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "mcp-smoke", "version": "0.1"},
    })
    init = read_until_id(1)
    results.append(("initialize", init is not None and "result" in (init or {})))

    send("notifications/initialized", {}, is_notification=True)

    send("tools/list", {})
    tl = read_until_id(2)
    tools = []
    if tl and "result" in tl:
        tools = [t["name"] for t in tl["result"].get("tools", [])]
    results.append(("tools/list", len(tools) > 0))
    print("TOOLS EXPOSED:", ", ".join(sorted(tools)))

    def call(tool, args):
        send("tools/call", {"name": tool, "arguments": args})
        resp = read_until_id(_id)
        ok = bool(resp) and "result" in resp and not resp["result"].get("isError")
        text = ""
        if resp and "result" in resp:
            for c in resp["result"].get("content", []):
                if c.get("type") == "text":
                    text += c["text"]
        return ok, text

    for tool, args in [
        ("git_status", {"repo_path": REPO}),
        ("git_log", {"repo_path": REPO, "max_count": 5}),
        ("git_diff_unstaged", {"repo_path": REPO}),
    ]:
        if tool not in tools:
            # fall back to git_diff if the unstaged variant isn't present
            if tool == "git_diff_unstaged" and "git_diff" in tools:
                tool, args = "git_diff", {"repo_path": REPO, "target": "HEAD"}
            else:
                results.append((tool, False))
                print(f"--- {tool}: NOT EXPOSED")
                continue
        ok, text = call(tool, args)
        results.append((tool, ok))
        print(f"--- {tool}: {'PASS' if ok else 'FAIL'}")
        print("\n".join(text.splitlines()[:12]))
        print()
finally:
    try:
        proc.stdin.close()
    except Exception:
        pass
    try:
        proc.terminate()
    except Exception:
        pass

print("=== SUMMARY ===")
allok = True
for name, ok in results:
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
    allok = allok and ok
sys.exit(0 if allok else 1)
