import argparse
import json
import os
from pathlib import Path

from .core import EstateAgent, Rejected
from .server import make_server


def load_env(path=Path(".env.local")):
    """Read KEY=VALUE lines into the environment; values already set in the shell win."""
    if path.exists():
        for line in path.read_text().splitlines():
            key, sep, value = line.strip().partition("=")
            if sep and key and not key.startswith("#"):
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def main():
    load_env()
    parser = argparse.ArgumentParser(description="Habilin synthetic estate-settlement demo")
    parser.add_argument("command", choices=["serve", "sessions", "code"], nargs="?", default="serve")
    parser.add_argument("--directory", type=Path, default=Path(".runtime"))
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--live-jev", action="store_true")
    parser.add_argument("--case", default="EST-001", help="Case for the owner code: EST-001 (Philippines) or EST-UK-001 (United Kingdom)")
    args = parser.parse_args()
    if args.command == "sessions":
        print((args.directory / "access.json").read_text())
    elif args.command == "code":
        try:
            print(EstateAgent(args.directory / "estate.db").issue_code(args.case))
        except Rejected as exc:
            parser.exit(1, f"{exc}\n")
    else:
        server = make_server(args.directory, args.port, args.live_jev)
        print(f"Habilin at http://127.0.0.1:{server.server_port} · ALL INSTITUTIONS SIMULATED", flush=True)
        link = "&".join(f"{role}={token}" for role, token in server.tokens.items())
        print(f"Demo link (all three roles): http://127.0.0.1:{server.server_port}/#{link}", flush=True)
        print(f"Owner one-time code, in a separate terminal: python3 -m habilin code --directory {args.directory} --case EST-001 (or EST-UK-001)", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()


if __name__ == "__main__":
    main()
