"""Run HTTP server for Integration API (sync for Phase 1)."""

from typing import Any

from cerebrain.api.routes import handle_brain_info, handle_chat, handle_health, handle_websocket


def run_server(brain_name: str | None = None, port: int = 17971) -> None:
    """Start a simple HTTP server (Phase 1: use uvicorn if available else basic)."""
    try:
        import uvicorn
        from fastapi import FastAPI, WebSocket
        from fastapi.middleware.cors import CORSMiddleware

        app = FastAPI(title="Cerebrain API")
        app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"])

        @app.post("/v1/chat")
        @app.post("/v1/messages")
        def post_chat(body: dict[str, Any]) -> dict[str, Any]:
            return handle_chat(body, brain_name)

        @app.get("/health")
        @app.get("/v1/status")
        def get_health() -> dict[str, str]:
            return handle_health()

        @app.get("/v1/brain")
        def get_brain() -> dict[str, Any]:
            return handle_brain_info(brain_name)

        @app.websocket("/v1/stream")
        async def ws_stream(websocket: WebSocket) -> None:
            await websocket.accept()
            await handle_websocket(websocket, brain_name)

        uvicorn.run(app, host="0.0.0.0", port=port)
    except ImportError:
        # No fastapi/uvicorn: run minimal server with stdlib
        from http.server import BaseHTTPRequestHandler, HTTPServer
        import json

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path in ("/health", "/v1/status"):
                    self._json(200, handle_health())
                elif self.path == "/v1/brain":
                    self._json(200, handle_brain_info(brain_name))
                else:
                    self.send_error(404)

            def do_POST(self):
                if self.path in ("/v1/chat", "/v1/messages"):
                    length = int(self.headers.get("Content-Length", 0))
                    body = json.loads(self.rfile.read(length).decode()) if length else {}
                    self._json(200, handle_chat(body, brain_name))
                else:
                    self.send_error(404)

            def _json(self, code: int, data: dict) -> None:
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(data).encode())

            def log_message(self, format, *args):  # noqa: A003
                pass

        server = HTTPServer(("0.0.0.0", port), Handler)
        from cerebrain import __logo__, __version__
        from rich.console import Console
        Console().print(f"{__logo__} API on http://0.0.0.0:{port} (stdlib server)")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.shutdown()
