"""E2E probe: async generate + check_task polling + resources/read, all in ONE server process."""

import json
import subprocess
import sys
import time

SERVER = sys.executable
SERVER_SCRIPT = __file__.rsplit("e2e_probe.py", 1)[0] + "server.py"

proc = subprocess.Popen(
    [SERVER, SERVER_SCRIPT],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    text=True, encoding="utf-8", bufsize=1,
)

def send(obj: dict) -> None:
    proc.stdin.write(json.dumps(obj, ensure_ascii=False) + "\n")
    proc.stdin.flush()

def recv(timeout: float = 300) -> dict:
    proc.stdout.readline()

def call(method: str, params: dict, msg_id: int) -> dict:
    send({"jsonrpc": "2.0", "id": msg_id, "method": method, "params": params})
    while True:
        line = proc.stdout.readline()
        if not line:
            raise RuntimeError("server closed")
        msg = json.loads(line)
        if msg.get("id") == msg_id:
            return msg

call("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                    "clientInfo": {"name": "e2e_probe", "version": "1"}}, 1)
send({"jsonrpc": "2.0", "method": "notifications/initialized"})

# 1) async generate
r = call("tools/call", {"name": "generate_image", "arguments": {
    "prompt": "A pixel art treasure chest with gold coins spilling out, 16-bit retro game style",
    "size": "1024x1024", "filename_prefix": "chest", "output_dir": "D:/VSAI/MCP/e2e_test_out",
    "wait": False}}, 2)
print("ASYNC:", r["result"]["content"][0]["text"])
task_id = json.loads(r["result"]["content"][0]["text"])["task_id"]

# 2) poll check_task until done
for i in range(24):
    time.sleep(5)
    r = call("tools/call", {"name": "check_task", "arguments": {"task_id": task_id}}, 3)
    txt = json.loads(r["result"]["content"][0]["text"])
    print(f"POLL[{i}]:", txt.get("status", txt))
    if txt.get("status") in ("completed", "failed"):
        break

# 3) resources/read assets://list
r = call("resources/read", {"uri": "assets://list"}, 4)
print("RESOURCE:", json.dumps(r["result"], ensure_ascii=False)[:600])

proc.terminate()
