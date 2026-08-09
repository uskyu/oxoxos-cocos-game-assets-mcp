"""Direct MCP stdio invoker: python invoke_cli.py <tool> '<json-args>'

Spawns the FastMCP server and performs a single tools/call over stdio JSON-RPC.
"""

import json
import subprocess
import sys

SERVER = sys.executable
SERVER_SCRIPT = __file__.rsplit("invoke_cli.py", 1)[0] + "server.py"


def main() -> int:
    tool = sys.argv[1]
    args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}

    proc = subprocess.Popen(
        [SERVER, SERVER_SCRIPT],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        bufsize=1,
    )

    def send(obj: dict) -> None:
        proc.stdin.write(json.dumps(obj, ensure_ascii=False) + "\n")
        proc.stdin.flush()

    def recv(timeout: float = 300) -> dict:
        return json.loads(proc.stdout.readline())

    send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "invoke_cli", "version": "0.1"},
    }})
    recv()
    send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    send({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
          "params": {"name": tool, "arguments": args}})
    while True:
        msg = recv()
        if msg.get("id") == 2:
            result = msg.get("result", {})
            for content in result.get("content", []):
                if content.get("type") == "text":
                    print(content["text"])
            if result.get("isError"):
                return 1
            return 0
        if "error" in msg:
            print(json.dumps(msg["error"], ensure_ascii=False))
            return 1


if __name__ == "__main__":
    sys.exit(main())
