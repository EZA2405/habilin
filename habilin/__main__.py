import argparse
import json
from pathlib import Path

from .core import EstateAgent, Rejected
from .server import make_server


def main():
    parser = argparse.ArgumentParser(description="Habilin synthetic estate-settlement demo")
    parser.add_argument("command", choices=["serve", "sessions", "code"], nargs="?", default="serve")
    parser.add_argument("--directory", type=Path, default=Path(".runtime"))
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--live-jev", action="store_true")
    args = parser.parse_args()
    if args.command == "sessions":
        print((args.directory / "access.json").read_text())
    elif args.command == "code":
        try:
            print(EstateAgent(args.directory / "estate.db").issue_code())
        except Rejected as exc:
            parser.exit(1, f"{exc}\n")
    else:
        server = make_server(args.directory, args.port, args.live_jev)
        print(f"Habilin at http://127.0.0.1:{server.server_port} · ALL INSTITUTIONS SIMULATED", flush=True)
        print("Use python3 -m habilin sessions in a separate terminal for demo role tokens.", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()


if __name__ == "__main__":
    main()
