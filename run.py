import subprocess
import sys
import asyncio
import websockets
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configuration
HTTP_PORT = 3331
WEBSOCKET_PORT = 5678
WATCH_DIR = "."


class FileChangeHandler(FileSystemEventHandler):
    """Watches for file changes and triggers a reload"""

    def __init__(self, loop, reload_callback):
        self.loop = loop
        self.reload_callback = reload_callback

    def on_any_event(self, event):
        print(event)
        if event.event_type in ("modified", "created", "deleted", "moved"):
            print(f"File changed: {event.src_path}. Reloading browser...")
            asyncio.run_coroutine_threadsafe(self.reload_callback(), self.loop)  # FIX: Ensure this runs in main loop


class LiveReloadServer:
    """Manages the HTTP server and WebSocket-based live reload"""

    def __init__(self):
        self.http_process = None
        self.clients = set()
        self.loop = asyncio.new_event_loop()  # Create an asyncio event loop

    def start_http_server(self):
        """Starts the Python HTTP server"""
        if self.http_process:
            self.http_process.terminate()
            self.http_process.wait()
        self.http_process = subprocess.Popen(
            [sys.executable, "-m", "http.server", str(HTTP_PORT), "--directory", WATCH_DIR],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print(f"Serving at: http://localhost:{HTTP_PORT}")

    async def notify_clients(self):
        """Sends a reload message to all connected WebSocket clients"""
        if not self.clients:
            return  # No clients connected, no need to send reload
        print("Reloading browser...")
        disconnected_clients = set()
        for client in self.clients:
            try:
                await client.send("reload")
            except websockets.exceptions.ConnectionClosedOK:
                disconnected_clients.add(client)  # Mark clients that disconnected
        self.clients -= disconnected_clients  # Remove disconnected clients

    async def websocket_handler(self, websocket):
        """Handles WebSocket connections from the browser"""
        self.clients.add(websocket)
        try:
            await websocket.wait_closed()
        finally:
            self.clients.discard(websocket)  # Remove client when it disconnects

    def start_watcher(self):
        """Watches for file changes and triggers reloads"""
        event_handler = FileChangeHandler(self.loop, self.notify_clients)
        observer = Observer()
        observer.schedule(event_handler, WATCH_DIR, recursive=True)
        observer.start()

        async def ws_server():
            async with websockets.serve(self.websocket_handler, "localhost", WEBSOCKET_PORT):
                await asyncio.Future()  # Keeps running

        # Run the WebSocket server inside a separate thread
        threading.Thread(target=self.run_loop, daemon=True).start()
        try:
            observer.join()
        except KeyboardInterrupt:
            observer.stop()
            if self.http_process:
                self.http_process.terminate()
            observer.join()

    def run_loop(self):
        """Runs the asyncio event loop in a separate thread"""
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.websocket_server())

    async def websocket_server(self):
        """Start the WebSocket server in the asyncio loop"""
        async with websockets.serve(self.websocket_handler, "localhost", WEBSOCKET_PORT):
            await asyncio.Future()  # Keeps running


if __name__ == "__main__":
    server = LiveReloadServer()
    server.start_http_server()
    server.start_watcher()
