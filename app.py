from flask import Flask, render_template, request
from flask_socketio import SocketIO, join_room
from game import Player, PokerRoom

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"
socketio = SocketIO(app)

# Global dictionary to track all rooms
rooms = {}

@app.route("/")
def index():
    return render_template("index.html")

@socketio.on("join_room")
def handle_join(data):
    name = data["name"]
    code = data["room"]

    global rooms

    # Create room if it doesn't exist
    if code not in rooms:
        rooms[code] = PokerRoom(code)

    room = rooms[code]
    player = Player(request.sid, name)

    if not room.add_player(player):
        return  # Room full

    join_room(code)
    print(f"{name} joined room {code} (SID {request.sid})")

    # Notify all players in the room
    socketio.emit("room_update", room.serialize(), room=code)

if __name__ == "__main__":
    socketio.run(app, debug=True)

@socketio.on("connect")
def handle_connect():
    print("Client connected")
