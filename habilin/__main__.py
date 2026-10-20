import argparse
import os
import webbrowser
from pathlib import Path

from .core import EstateAgent, Rejected
from .server import make_server


def load_env(path=Path(".env.local")):
    """Read KEY=VALUE lines into the environment; values already set in the shell win."""
    if path.exists():
        for line in path.read_text().splitlines():
            key, sep, value = line.strip().partition("=")
            if sep and key and value.strip() and not key.startswith("#"):
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def main():
    load_env()
    parser = argparse.ArgumentParser(description="Habilin synthetic estate-settlement demo")
    parser.add_argument("command", choices=["serve", "sessions", "code"], nargs="?", default="serve")
    parser.add_argument("--directory", type=Path, default=Path(".runtime"))
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--live-jev", action="store_true")
    parser.add_argument("--no-open", action="store_true", help="Do not open the browser signed in to the demo")
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
        try:
            server = make_server(args.directory, args.port, args.live_jev)
        except OSError:
            # Port taken by another app: let the OS pick a free one.
            server = make_server(args.directory, 0, args.live_jev)
        url = f"http://127.0.0.1:{server.server_port}"
        print(f"Habilin at {url} · ALL INSTITUTIONS SIMULATED · opens signed in to the local demo", flush=True)
        if not args.no_open:
            webbrowser.open(url)
        print(f"Owner one-time code, in a separate terminal: python3 -m habilin code --directory {args.directory} --case EST-001 (or EST-UK-001)", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()


if __name__ == "__main__":
    main()
