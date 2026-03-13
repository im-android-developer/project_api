import json
import threading
import time
from flask import Flask, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'f9e4bbf6ee3e71f192f45073e9bf025bbb9d3438e216482e487f3233ca7668de'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Load JSON data
def load_ticks_data():
    """Load tick data from index_ticks.json"""
    try:
        with open('index_ticks.json', 'r') as f:
            data = json.load(f)
            return data.get('events', [])
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading ticks data: {e}")
        return []

# Global state
ticks_data = load_ticks_data()
connected_clients = set()
broadcast_threads = {}  # Track broadcast thread per client


class TickBroadcaster:
    """Manages tick broadcasting for a client"""
    
    def __init__(self, client_id):
        self.client_id = client_id
        self.current_index = 0
        self.running = False
        self.thread = None
    
    def start(self):
        """Start broadcasting ticks"""
        if self.running:
            return
        
        self.running = True
        self.current_index = 0
        self.thread = threading.Thread(target=self._broadcast_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop broadcasting"""
        self.running = False
    
    def _broadcast_loop(self):
        """Main broadcast loop - sends tick every 3 seconds"""
        while self.running and self.current_index < len(ticks_data):
            if self.client_id not in connected_clients:
                self.running = False
                break
            
            event = ticks_data[self.current_index]
            
            # Only emit if event has data
            if event and 'sequence' in event:
                socketio.emit('tick_data', {
                    'status': 'OK',
                    'data': event,
                    'is_last': self.current_index == len(ticks_data) - 1
                }, room=self.client_id)
                
                print(f"Sent sequence {event.get('sequence')} to client {self.client_id}")
            
            self.current_index += 1
            
            # Wait 3 seconds before next tick
            if self.running and self.current_index < len(ticks_data):
                time.sleep(3)
        
        # Reached end of data
        if self.running and self.current_index >= len(ticks_data):
            socketio.emit('tick_data', {
                'status': 'COMPLETED',
                'message': 'All sequences sent. Reconnect to restart.',
                'total_sequences': len(ticks_data)
            }, room=self.client_id)
            self.running = False
            print(f"Broadcast completed for client {self.client_id}")


@app.route("/")
def home():
    return jsonify({
        "message": "WebSocket Tick Server Running",
        "websocket_endpoint": "/socket.io/",
        "total_sequences": len(ticks_data)
    })


@app.route("/api/ticks/info")
def ticks_info():
    """Get info about available tick data"""
    return jsonify({
        "status": "OK",
        "total_sequences": len(ticks_data),
        "connected_clients": len(connected_clients),
        "broadcast_interval": "3 seconds"
    })


@socketio.on('connect')
def handle_connect():
    """Handle new WebSocket connection"""
    client_id = str(id(socketio))
    from flask import request
    client_id = request.sid
    
    connected_clients.add(client_id)
    print(f"Client connected: {client_id}")
    
    emit('connection_status', {
        'status': 'connected',
        'client_id': client_id,
        'total_sequences': len(ticks_data),
        'message': 'Send "start_ticks" event to begin receiving data'
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    from flask import request
    client_id = request.sid
    
    # Stop broadcaster if running
    if client_id in broadcast_threads:
        broadcast_threads[client_id].stop()
        del broadcast_threads[client_id]
    
    connected_clients.discard(client_id)
    print(f"Client disconnected: {client_id}")


@socketio.on('start_ticks')
def handle_start_ticks():
    """Start broadcasting ticks to the client"""
    from flask import request
    client_id = request.sid
    
    # Stop existing broadcaster if any
    if client_id in broadcast_threads:
        broadcast_threads[client_id].stop()
    
    # Reload data in case it was updated
    global ticks_data
    ticks_data = load_ticks_data()
    
    if not ticks_data:
        emit('tick_data', {
            'status': 'Error',
            'message': 'No tick data available'
        })
        return
    
    # Create and start new broadcaster
    broadcaster = TickBroadcaster(client_id)
    broadcast_threads[client_id] = broadcaster
    broadcaster.start()
    
    emit('tick_data', {
        'status': 'STARTED',
        'message': 'Tick broadcasting started',
        'total_sequences': len(ticks_data)
    })


@socketio.on('stop_ticks')
def handle_stop_ticks():
    """Stop broadcasting ticks to the client"""
    from flask import request
    client_id = request.sid
    
    if client_id in broadcast_threads:
        broadcast_threads[client_id].stop()
        del broadcast_threads[client_id]
        
        emit('tick_data', {
            'status': 'STOPPED',
            'message': 'Tick broadcasting stopped'
        })
    else:
        emit('tick_data', {
            'status': 'Info',
            'message': 'No active broadcast to stop'
        })


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", "5001"))
    print(f"Starting WebSocket Tick Server on port {port}")
    print(f"Loaded {len(ticks_data)} tick sequences")
    socketio.run(app, host="0.0.0.0", port=port, debug=False)
