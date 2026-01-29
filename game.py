# ============================================================================
# POKER CHIP TRACKER - GAME LOGIC
# Core classes for poker room and player management
# NOTE: Used CoPilot for code organization and easy understanding
# ============================================================================

# ============================================================================
# PLAYER CLASS
# ============================================================================

class Player:
    """
    Represents a single player in the poker game.
    Tracks their socket ID, name, and chip count.
    """
    
    def __init__(self, sid, name, starting_chips=10):
        """
        Initialize a new player.
        
        Args:
            sid: Socket.IO session ID (unique identifier)
            name: Player's display name
            starting_chips: Initial chip count (default: 10)
        """
        self.sid = sid
        self.name = name
        self.chips = starting_chips
        
    def serialize(self):
        """
        Convert player data to dictionary for JSON transmission.
        Note: SID is not included for security (only sent to server).
        """
        return {
            "name": self.name,
            "chips": self.chips
        }

# ============================================================================
# POKER ROOM CLASS
# ============================================================================

class PokerRoom:
    """
    Manages a poker game room including players, betting, and game state.
    Supports up to 10 players with configurable blinds and starting chips.
    """
    
    def __init__(self, code, leader_sid=None):
        """
        Initialize a new poker room.
        
        Args:
            code: Unique room code (5-character alphanumeric)
            leader_sid: Socket ID of room creator (has special permissions)
        """
        # Room identification
        self.code = code
        self.leader_sid = leader_sid
        
        # Player management
        self.players = []  # List of Player objects
        self.in_hand = []  # Players still active in current hand
        self.players_to_act = set()  # SIDs of players who need to act
        
        # Game state
        self.pot = 0
        self.current_bet = 0
        self.bets = {}  # {player_sid: amount_bet_this_round}
        self.round = "preflop"  # preflop, flop, turn, river, showdown
        self.community_cards = []  # Not used (manual chip tracking only)
        
        # Position tracking
        self.dealer_index = 0
        self.small_blind_index = 0
        self.big_blind_index = 1
        self.turn_index = 0
        
        # UI state flags
        self.hand_started = False  # Whether a hand is currently in progress
        self.show_config = False  # Whether to show settings panel (leader only)
        
        # Configurable settings
        self.starting_chips = 10.00
        self.small_blind_amount = 0.10
        self.big_blind_amount = 0.20
        self.game_configured = False  # Whether leader has set custom settings

    # ========================================================================
    # PLAYER MANAGEMENT
    # ========================================================================

    def add_player(self, player):
        """
        Add a player to the room.
        
        Args:
            player: Player object to add
            
        Returns:
            bool: True if added, False if room full (max 10 players)
        """
        if len(self.players) >= 10:
            return False
        self.players.append(player)
        return True
    
    def remove_player(self, player_sid):
        """
        Remove a player completely from the room.
        Cleans up all references in game state and adjusts indices.
        
        Args:
            player_sid: Socket ID of player to remove
            
        Returns:
            bool: True if removed, False if player not found
        """
        # Find player
        player = next((p for p in self.players if p.sid == player_sid), None)
        if not player:
            return False
    
        player_index = self.players.index(player)
    
        # Remove from all data structures
        self.players.remove(player)
        self.in_hand = [p for p in self.in_hand if p.sid != player_sid]
        self.players_to_act.discard(player_sid)
        self.bets.pop(player_sid, None)
    
        # Adjust position indices (shift down if removed player was before index)
        n = len(self.players)
        if n > 0:
            if player_index <= self.dealer_index:
                self.dealer_index = max(0, self.dealer_index - 1)
            if player_index <= self.small_blind_index:
                self.small_blind_index = max(0, self.small_blind_index - 1)
            if player_index <= self.big_blind_index:
                self.big_blind_index = max(0, self.big_blind_index - 1)
            if player_index <= self.turn_index:
                self.turn_index = max(0, self.turn_index - 1)
    
        # Transfer leadership if leader left
        if self.leader_sid == player_sid and len(self.players) > 0:
            self.leader_sid = self.players[0].sid
    
        return True

    # ========================================================================
    # GAME CONFIGURATION
    # ========================================================================
    
    def configure_game(self, starting_chips, small_blind, big_blind):
        """
        Set game parameters (leader only, typically before first hand).
        Updates all existing players' chip counts to match.
        
        Args:
            starting_chips: Initial chip count for all players
            small_blind: Small blind amount
            big_blind: Big blind amount
        """
        self.starting_chips = starting_chips
        self.small_blind_amount = small_blind
        self.big_blind_amount = big_blind
        self.game_configured = True
        
        # Update existing players
        for player in self.players:
            player.chips = starting_chips

    # ========================================================================
    # HAND MANAGEMENT
    # ========================================================================
    
    def start_hand(self):
        """
        Initialize a new hand: rotate dealer, set blinds, reset betting.
        """
        self.hand_started = True
        self.round = "preflop"
        self.pot = 0
        self.current_bet = 0
        
        # All players active
        self.in_hand = self.players.copy()
        self.players_to_act = {p.sid for p in self.in_hand}
        self.bets = {p.sid: 0 for p in self.players}

        n = len(self.players)
        if n < 2:
            return  # Need at least 2 players

        # Rotate dealer button
        self.dealer_index = (self.dealer_index + 1) % n
        
        # Set blinds relative to dealer
        self.small_blind_index = (self.dealer_index + 1) % n
        self.big_blind_index = (self.dealer_index + 2) % n

        # First to act preflop is after big blind
        self.turn_index = (self.big_blind_index + 1) % n
    
    def is_hand_over(self):
        """
        Check if hand should end (only 1 player left or showdown reached).
        
        Returns:
            bool: True if hand is over
        """
        return len(self.in_hand) <= 1 or self.round == "done"
    
    def award_pot_to_winner(self):
        """
        Award pot to last remaining player (used when everyone else folds).
        
        Returns:
            Player: Winner object, or None if no clear winner
        """
        if len(self.in_hand) == 1:
            winner = self.in_hand[0]
            winner.chips += self.pot
            print(f"{winner.name} wins {self.pot} chips!")
            self.pot = 0
            return winner
        return None

    # ========================================================================
    # BETTING ROUND MANAGEMENT
    # ========================================================================
    
    def betting_round_complete(self):
        """
        Check if all players have acted this round.
        
        Returns:
            bool: True if round is complete
        """
        return len(self.players_to_act) == 0
    
    def advance_round(self):
        """
        Move to next betting round (preflop -> flop -> turn -> river).
        Resets betting state for new round.
        """
        print("ADVANCE ROUND CALLED FROM", self.round)
        
        # Reset betting for new round
        self.players_to_act = {p.sid for p in self.in_hand}
        self.current_bet = 0
        self.bets = {p.sid: 0 for p in self.players}

        # Advance to next round
        if self.round == "preflop":
            self.round = "flop"
        elif self.round == "flop":
            self.round = "turn"
        elif self.round == "turn":
            self.round = "river"
        elif self.round == "river":
            self.round = "done"
            return
        
        # First to act post-flop is small blind (or next active player)
        self.turn_index = self.small_blind_index
        self._skip_to_next_active()

    # ========================================================================
    # TURN MANAGEMENT
    # ========================================================================
    
    def get_current_player(self):
        """
        Get the player whose turn it is.
        Automatically skips folded players.
        
        Returns:
            Player: Current player, or None if hand is over
        """
        if self.round == "done" or not self.players:
            return None

        self._skip_to_next_active()
        return self.players[self.turn_index]
        
    def advance_turn(self):
        """Move to next player's turn (skips folded players)."""
        n = len(self.players)
        if n == 0:
            return

        self.turn_index = (self.turn_index + 1) % n
        self._skip_to_next_active()
    
    def _skip_to_next_active(self):
        """
        Helper: Move turn index to next player still in hand.
        Prevents turn getting stuck on folded players.
        """
        n = len(self.players)
        if n == 0:
            return

        start = self.turn_index
        while self.players[self.turn_index] not in self.in_hand:
            self.turn_index = (self.turn_index + 1) % n
            if self.turn_index == start:
                break  #all players folded
    
    def process_action_and_advance(self):
        """
        Central method that determines game flow after a player action.
        Handles: ending hand, advancing to next round, or advancing to next player.
        
        Returns:
            str: The action taken - 'end_hand', 'advance_round', or 'advance_turn'
        """
        #checks if one player is left (they get the pot)
        if self.is_hand_over():
            self.award_pot_to_winner()
            return 'end_hand'
        
        #checks if complete
        elif self.betting_round_complete():
            self.advance_round()
            return 'advance_round'
        
        else:
            self.advance_turn()
            return 'advance_turn'

    # ========================================================================
    # BETTING ACTIONS
    # ========================================================================
    
    def place_bet(self, player_sid, amount):
        """
        Place a bet (used for blinds and raises).
        
        Args:
            player_sid: Socket ID of player
            amount: Chips to bet
            
        Returns:
            bool: True if successful, False if not enough chips
        """
        player = next((p for p in self.players if p.sid == player_sid), None)
        if not player:
            return False
        if amount > player.chips:
            return False
            
        player.chips -= amount
        self.pot += amount
        self.current_bet = max(self.current_bet, amount)
        self.bets[player_sid] += amount
        return True
    
    def can_check(self, player_sid):
        """
        Check if player can check (already matched current bet).
        
        Args:
            player_sid: Socket ID of player
            
        Returns:
            bool: True if can check
        """
        return self.current_bet == self.bets[player_sid]

    def call(self, player_sid):
        """
        Match the current bet.
        
        Args:
            player_sid: Socket ID of player
            
        Returns:
            bool: True if successful
        """
        player = next(p for p in self.players if p.sid == player_sid)
        call_amount = self.current_bet - self.bets[player_sid]

        if call_amount <= 0:
            return True  # Already matched

        # All-in if not enough chips
        if call_amount > player.chips:
            call_amount = player.chips

        player.chips -= call_amount
        self.pot += call_amount
        self.bets[player_sid] += call_amount
        return True
    
    def raise_bet(self, player_sid, raise_amount):
        """
        Raise the current bet.
        
        Args:
            player_sid: Socket ID of player
            raise_amount: Additional chips to bet beyond call amount
            
        Returns:
            bool: True if successful, False if not enough chips
        """
        player = next(p for p in self.players if p.sid == player_sid)

        # Calculate total needed (call + raise)
        call_amount = self.current_bet - self.bets[player_sid]
        total_needed = call_amount + raise_amount

        if total_needed > player.chips:
            return False

        player.chips -= total_needed
        self.pot += total_needed
        self.bets[player_sid] += total_needed
        self.current_bet += raise_amount
        return True
    
    def fold_current_player(self):
        """
        Remove current player from hand (they folded).
        Cleans up their betting state.
        """
        player = self.get_current_player()
        if not player:
            return

        # Remove from active players
        self.in_hand = [p for p in self.in_hand if p.sid != player.sid]
        self.players_to_act.discard(player.sid)
        self.bets.pop(player.sid, None)

    # ========================================================================
    # DATA SERIALIZATION
    # ========================================================================

    def serialize(self):
        """
        Convert room state to dictionary for JSON transmission to clients.
        
        Returns:
            dict: Complete room state including players, pot, turn, settings
        """
        current = self.get_current_player()
        call_amount = 0
        if current:
            call_amount = self.current_bet - self.bets.get(current.sid, 0)

        return {
            # Room info
            "code": self.code,
            "leader_sid": self.leader_sid,
            
            # Players
            "players": [p.serialize() for p in self.players],
            "current_turn": self.get_current_player().name if self.get_current_player() else None,
            "dealer": self.players[self.dealer_index].name if self.players else None,
            
            # Game state
            "pot": self.pot,
            "call_amount": call_amount,
            "round": self.round,
            "community_cards": self.community_cards,
            
            # Settings
            "game_configured": self.game_configured,
            "starting_chips": self.starting_chips,
            "small_blind": self.small_blind_amount,
            "big_blind": self.big_blind_amount,
            
            # UI flags
            "hand_started": self.hand_started,
            "show_config": self.show_config
        }
