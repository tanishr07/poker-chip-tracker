# ============================================================================
# POKER CHIP TRACKER - SERVER
# Flask + Socket.IO backend for real-time multiplayer poker chip tracking
# ============================================================================

from flask import Flask, render_template, request
from flask_socketio import SocketIO, join_room
from flask_cors import CORS
from game import Player, PokerRoom
import random
import string

# ============================================================================
# APP INITIALIZATION
# ============================================================================

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"
socketio = SocketIO(app, cors_allowed_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:5000"])
CORS(app)

# Global dictionary to track all active rooms: {room_code: PokerRoom}
rooms = {}

# ============================================================================
# HTTP ROUTES
# ============================================================================

@app.route("/")
def index():
    """Serve the main HTML page"""
    return render_template("index.html")

# ============================================================================
# ROOM MANAGEMENT HANDLERS
# ============================================================================

@socketio.on("create_room")
def handle_create_room(data):
    """
    Create a new poker room with a random 5-character code.
    The creator becomes the room leader and first player.
    """
    name = data["name"]
    global rooms
    
    #generate alphanumeric room code
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        if code not in rooms:
            break
    
    rooms[code] = PokerRoom(code, leader_sid=request.sid)
    room = rooms[code]
    
    #makes room creator a player
    player = Player(request.sid, name, starting_chips=room.starting_chips)
    room.add_player(player)
    
    join_room(code)
    print(f"{name} created and joined room {code} (SID {request.sid})")
    
    socketio.emit("room_created", {"code": code}, room=request.sid)
    socketio.emit("room_update", room.serialize(), room=code)

@socketio.on("join_room")
def handle_join(data):
    """
    Allow a player to join an existing room.
    Creates room if it doesn't exist.
    """
    name = data["name"]
    code = data["room"]
    global rooms

    #validate room code exists
    if code not in rooms:
        socketio.emit('join_error', {'message': f'Room code "{code}" does not exist. Please check the code and try again.'})
        return

    room = rooms[code]
    player = Player(request.sid, name, starting_chips=room.starting_chips)

    #check if room is full
    if not room.add_player(player):
        return  

    join_room(code)
    print(f"{name} joined room {code} (SID {request.sid})")
    
    #broadcast
    socketio.emit("action_log", {"message": f"{name} has joined the room."}, room=code)
    socketio.emit("room_update", room.serialize(), room=code)

@socketio.on("leave_room")
def handle_leave_room(data):
    """
    Remove a player from the room.
    Deletes room if last player leaves.
    """
    room_code = data["room"]
    room = rooms.get(room_code)
    if not room:
        return

    #find player
    player = next((p for p in room.players if p.sid == request.sid), None)
    if not player:
        return

    room.remove_player(request.sid)
    
    #clean up empty room
    if len(room.players) == 0:
        del rooms[room_code]
        socketio.emit("action_log", {"message": f"Room {room_code} has been closed as the last player left."})
        return
    
    #broadcast
    socketio.emit("action_log", {"message": f"{player.name} has left the room."}, room=room_code)
    socketio.emit("room_update", room.serialize(), room=room_code)

# ============================================================================
# GAME CONFIGURATION HANDLERS (LEADER ONLY)
# ============================================================================

@socketio.on("configure_game")
def handle_configure_game(data):
    """
    Set starting chips and blind amounts for the room.
    Only the room leader can configure these settings.
    """
    room_code = data["room"]
    starting_chips = float(data["starting_chips"])
    small_blind = float(data["small_blind"])
    big_blind = float(data["big_blind"])
    
    room = rooms.get(room_code)
    if not room:
        return
    
    #check if leader
    if room.leader_sid != request.sid:
        socketio.emit("error", {"message": "Only the room leader can configure settings"}, room=request.sid)
        return
    
    room.configure_game(starting_chips, small_blind, big_blind)
    
    #broadcast
    socketio.emit("action_log", {"message": f"⚙️ Game configured: ${starting_chips:.2f} starting, Blinds ${small_blind:.2f}/${big_blind:.2f}"}, room=room_code)
    socketio.emit("room_update", room.serialize(), room=room_code)

@socketio.on("open_config")
def handle_open_config(data):
    """
    Show the configuration panel (leader only).
    Uses server-driven UI pattern.
    """
    room_code = data["room"]
    room = rooms.get(room_code)
    if not room:
        return
    
    # Permission check: Only leader can open config
    if room.leader_sid != request.sid:
        socketio.emit("error", {"message": "Only the room leader can open settings"}, room=request.sid)
        return
    
    room.show_config = True
    socketio.emit("room_update", room.serialize(), room=room_code)

@socketio.on("close_config")
def handle_close_config(data):
    """
    Hide the configuration panel (leader only).
    """
    room_code = data["room"]
    room = rooms.get(room_code)
    if not room:
        return
    
    # Permission check: Only leader can close config
    if room.leader_sid != request.sid:
        socketio.emit("error", {"message": "Only the room leader can close settings"}, room=request.sid)
        return
    
    room.show_config = False
    socketio.emit("room_update", room.serialize(), room=room_code)

# ============================================================================
# HAND MANAGEMENT HANDLERS
# ============================================================================

@socketio.on("start_hand")
def handle_start_hand(data):
    """
    Start a new hand: rotate dealer, post blinds, reset betting.
    """
    code = data["code"]
    room = rooms[code]
    
    # Mark hand as started and hide config panel
    room.hand_started = True
    room.show_config = False

    # Initialize hand (rotates dealer, sets blinds)
    room.start_hand()

    # Post blinds
    sb = room.players[room.small_blind_index]
    bb = room.players[room.big_blind_index]
    room.place_bet(sb.sid, room.small_blind_amount)
    room.place_bet(bb.sid, room.big_blind_amount)

    # Log and broadcast
    socketio.emit("action_log", {"message": f"--- New Hand Started ---"}, room=code)
    socketio.emit("action_log", {"message": f"{sb.name} posts small blind (${room.small_blind_amount:.2f})"}, room=code)
    socketio.emit("action_log", {"message": f"{bb.name} posts big blind (${room.big_blind_amount:.2f})"}, room=code)
    socketio.emit("room_update", room.serialize(), room=code)

@socketio.on("declare_winner")
def handle_declare_winner(data):
    """
    Manually declare a winner and award them the pot.
    Used for chip tracking without actual card dealing.
    Only leader can declare winner.
    """
    room_code = data["room"]
    winner_name = data["winner"]
    
    room = rooms.get(room_code)
    if not room:
        return
    
    # Mark hand as ended
    room.hand_started = False
    
    # Permission check: Only leader can declare winner
    if room.leader_sid != request.sid:
        socketio.emit("error", {"message": "Only the room leader can declare the winner"}, room=request.sid)
        return
    
    # Find winner and award pot
    winner = next((p for p in room.players if p.name == winner_name), None)
    if not winner:
        return
    
    winner.chips += room.pot
    pot_amount = room.pot
    room.pot = 0
    room.round = "done"
    
    # Log and broadcast
    socketio.emit("action_log", {"message": f"💰 {winner_name} wins ${pot_amount:.2f}!"}, room=room_code)
    socketio.emit("room_update", room.serialize(), room=room_code)
    socketio.emit("hand_over", {"winner": winner_name, "pot": pot_amount}, room=room_code)

# ============================================================================
# PLAYER ACTION HANDLERS
# ============================================================================

@socketio.on("action")
def handle_action(data):
    """
    Process player betting actions: fold, check, call, raise.
    Validates turn order and manages betting rounds.
    """
    room_code = data["room"]
    action_type = data["action"]
    amount = data.get("amount", 0)

    room = rooms.get(room_code)
    if not room:
        return

    # Auto-start hand if not already started (legacy behavior)
    if not room.in_hand or len(room.in_hand) == 0:
        room.start_hand()

    # Validate it's this player's turn
    player = room.get_current_player()
    if player is None or player.sid != request.sid:
        socketio.emit("action_log", {"message": "Not your turn!"}, room=room_code)  
        return

    # Process different action types
    if action_type == "fold":
        room.players_to_act.discard(player.sid)
        room.fold_current_player()
        socketio.emit("action_log", {"message": f"{player.name} folds"}, room=room_code)

    elif action_type == "check":
        if not room.can_check(player.sid):
            return  # Can't check - need to call or fold
        room.players_to_act.discard(player.sid)
        socketio.emit("action_log", {"message": f"{player.name} checks"}, room=room_code)

    elif action_type == "call":
        call_amount = room.current_bet - room.bets[player.sid]
        room.call(player.sid)
        room.players_to_act.discard(player.sid)
        socketio.emit("action_log", {"message": f"{player.name} calls {call_amount}"}, room=room_code)
        
    elif action_type == "raise":
        if amount <= 0:
            return  # Invalid raise amount
        if not room.raise_bet(player.sid, amount):
            return  # Not enough chips
        # Reset players to act (everyone except raiser needs to respond)
        room.players_to_act = {p.sid for p in room.in_hand if p.sid != player.sid}
        socketio.emit("action_log", {"message": f"{player.name} raises ${amount:.2f}"}, room=room_code)

    # ========================================================================
    # GAME FLOW - Centralized turn advancement logic
    # ========================================================================
    
    game_action = room.process_action_and_advance()
    socketio.emit("room_update", room.serialize(), room=room_code)
    
    if game_action == 'end_hand':
        socketio.emit("hand_over", {"winner": room.players[0].name if room.in_hand else "Unknown", "pot": 0}, room=room_code)
    elif game_action == 'advance_round':
        socketio.emit("action_log", {"message": f"--- {room.round.upper()} ---"}, room=room_code)
    
    # Debug logging
    print(
        "ROUND:", room.round,
        "TURN:", room.players[room.turn_index].name,
        "IN_HAND:", [p.name for p in room.in_hand],
        "TO_ACT:", room.players_to_act
    )

# ============================================================================
# CONNECTION HANDLERS
# ============================================================================

@socketio.on("connect")
def handle_connect():
    """Log when a client connects"""
    print("Client connected")

@socketio.on("disconnect")
def handle_disconnect():
    """
    Auto-remove player from room when they disconnect.
    Prevents ghost players from blocking game progress.
    """
    # Find which room this player is in
    for room_code, room in list(rooms.items()):
        player = next((p for p in room.players if p.sid == request.sid), None)
        if player:
            room.remove_player(request.sid)
            
            # Delete empty rooms
            if len(room.players) == 0:
                del rooms[room_code]
            else:
                # Notify remaining players
                socketio.emit("action_log", {"message": f"{player.name} disconnected."}, room=room_code)
                socketio.emit("room_update", room.serialize(), room=room_code)
            break

# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    socketio.run(app, debug=True)
