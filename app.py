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

@socketio.on("action")
def handle_action(data):
    room_code = data["room"]
    action_type = data["action"]
    amount = data.get("amount", 0)

    room = rooms.get(room_code)
    if not room:
        return

    # START HAND if not already started
    if not room.in_hand or len(room.in_hand) == 0:
        room.start_hand()

    player = room.get_current_player() # get the player whose turn it is
    if  player is None or player.sid != request.sid:
        print("Not your turn!")
        return

    if action_type == "fold":
        room.players_to_act.discard(player.sid)
        room.fold_current_player()

    elif action_type == "check":
        if not room.can_check(player.sid):
            return
        room.players_to_act.discard(player.sid)

    elif action_type == "call":
        room.call(player.sid)
        room.players_to_act.discard(player.sid)
    elif action_type == "raise":
        if amount <= 0:
            return
        if not room.raise_bet(player.sid, amount):
            return
        room.players_to_act = {p.sid for p in room.in_hand if p.sid != player.sid}
# 🔑 SINGLE point of turn control
    # Check if only one player remains (everyone else folded)
    if room.is_hand_over():
        winner = room.award_pot_to_winner()
        socketio.emit("room_update", room.serialize(), room=room_code)
        if winner:
            socketio.emit("hand_over", {"winner": winner.name, "pot": 0}, room=room_code)
    elif room.betting_round_complete():
        room.advance_round()
        socketio.emit("room_update", room.serialize(), room=room_code)
    else:
        room.advance_turn()
        socketio.emit("room_update", room.serialize(), room=room_code)
    
    print(
    "ROUND:", room.round,
    "TURN:", room.players[room.turn_index].name,
    "IN_HAND:", [p.name for p in room.in_hand],
    "TO_ACT:", room.players_to_act
)


@socketio.on("start_hand")
def handle_start_hand(data):
    code = data["code"]
    room = rooms[code]

    room.start_hand()

    # Post blinds (NO turn advancement here)
    sb = room.players[room.small_blind_index]
    bb = room.players[room.big_blind_index]

    room.place_bet(sb.sid, 5)
    room.place_bet(bb.sid, 10)

    socketio.emit("room_update", room.serialize(), room=code)
    



if __name__ == "__main__":
    socketio.run(app, debug=True)

@socketio.on("connect")
def handle_connect():
    print("Client connected")
