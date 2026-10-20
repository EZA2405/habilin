"""Loopback-only demo server. Bearer credentials bind identities on the server."""

import json
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from .core import CASE_ID, SEEDS, EstateAgent, Principal, Rejected, digest
from .intents import classify, reply

STATIC = Path(__file__).with_name("static")


def make_server(directory, port=8765, live=False):
    directory = Path(directory)
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    directory.chmod(0o700)
    agent = EstateAgent(directory / "estate.db")
    (directory / "estate.db").chmod(0o600)
    identities = {"operator": "demo-operator", "owner": "demo-owner", "professional": "demo-cpa"}
    access_path = directory / "access.json"
    if access_path.exists():
        tokens = json.loads(access_path.read_text())
    else:
        tokens = {role: secrets.token_urlsafe(32) for role in identities}
        access_path.write_text(json.dumps(tokens, indent=2))
    access_path.chmod(0o600)
    principals = {token: (identities[role], role) for role, token in tokens.items()}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def respond(self, status, payload, content_type="application/json"):
            data = json.dumps(payload).encode() if content_type == "application/json" else payload
            self.send_response(status)
            for key, value in {
                "Content-Type": content_type, "Content-Length": str(len(data)),
                "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff",
                "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'",
                "Referrer-Policy": "no-referrer", "X-Frame-Options": "DENY",
            }.items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(data)

        def principal(self):
            actual_port = self.server.server_port
            allowed_hosts = {f"127.0.0.1:{actual_port}", f"localhost:{actual_port}"}
            if self.headers.get("Host") not in allowed_hosts:
                raise Rejected("Host is not allowed.")
            origin = self.headers.get("Origin")
            if origin and origin not in {f"http://{h}" for h in allowed_hosts}:
                raise Rejected("Origin is not allowed.")
            token = self.headers.get("Authorization", "").removeprefix("Bearer ")
            if not token.isascii():
                raise Rejected("A valid ASCII demo session token is required.")
            case_id = self.headers.get("X-Case-Id", CASE_ID)
            if case_id not in SEEDS:
                raise Rejected("Unknown case.")
            for known, (subject, role) in principals.items():
                if secrets.compare_digest(token, known):
                    return Principal(subject, role, case_id)
            raise Rejected("A valid demo session token is required.")

        def do_GET(self):
            path = urlsplit(self.path).path
            files = {"/": ("index.html", "text/html; charset=utf-8"),
                     "/app.js": ("app.js", "text/javascript"), "/style.css": ("style.css", "text/css")}
            if path in files:
                filename, mime = files[path]
                self.respond(200, (STATIC / filename).read_bytes(), mime)
                return
            try:
                principal = self.principal()
                case = agent.view(principal)
                if path == "/api/state":
                    self.respond(200, {"case": case, "packet_hash": digest(case["packet"]) if case["packet"] else None,
                                       "mode": "Live Jev · TypeSafe" if live else "Offline fixture routing"})
                elif path == "/api/packet":
                    self.respond(200, {"packet": case["packet"], "filing_receipt": case["filing_receipt"],
                                       "payment_receipt": case["payment_receipt"], "open_steps": case["open_steps"], "simulated": True})
                else:
                    self.respond(404, {"error": "Not found."})
            except Rejected as exc:
                self.respond(403, {"error": str(exc)})

        def do_POST(self):
            try:
                principal = self.principal()
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 8192 or self.headers.get_content_type() != "application/json":
                    raise Rejected("Use a bounded JSON request.")
                body = json.loads(self.rfile.read(length))
                if not isinstance(body, dict):
                    raise Rejected("Request must be an object.")
                if self.path == "/api/message":
                    if set(body) != {"text"}:
                        raise Rejected("Only a text message is accepted; chat cannot grant roles or approvals.")
                    classification = classify(body["text"], live)
                    case = agent.advance(principal) if classification["intent"] == "progress" else agent.view(principal)
                    with agent.connection() as db:
                        agent._event(db, principal, "classify_intent", json.dumps(classification))
                    self.respond(200, {"reply": reply(classification["intent"], case), "classification": classification})
                elif self.path == "/api/tool":
                    if set(body) != {"name", "args"} or not isinstance(body["args"], dict) or not isinstance(body["name"], str):
                        raise Rejected("Use a named tool with explicit arguments.")
                    agent.tool(principal, body["name"], **body["args"])
                    self.respond(200, {"ok": True})
                else:
                    self.respond(404, {"error": "Not found."})
            except (Rejected, ValueError, TypeError) as exc:
                self.respond(400, {"error": str(exc)})
            except Exception:
                self.respond(500, {"error": "The operation failed. Check case status before retrying."})

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.agent = agent
    server.tokens = tokens
    return server
