class Player:
    def __init__(self, sid, name):
        self.sid = sid
        self.name = name
        self.chips = 1000
        
    def serialize(self):
        return {
            "name": self.name,
            "chips": self.chips
        }
        
class PokerRoom:
    def __init__(self, code):
        self.code = code
        self.players = []
        self.turn_index = 0 #who's turn it is
        self.dealer_index = 0 #who's the dealer
        self.pot = 0 #keep track of the pot
        self.current_bet = 0 #current bet to call
        self.in_hand = [] #players still in the hand
        self.bets = {} #track bets this round
        self.community_cards = [] #cards on the table
        self.round = "preflop"  # preflop, flop, turn, river, showdown
        self.small_blind_index = 0
        self.big_blind_index = 1
        self.turn_index = 0
        self.players_to_act = set()


        
    def _skip_to_next_active(self):
        n = len(self.players)
        if n == 0:
            return

        start = self.turn_index
        while self.players[self.turn_index] not in self.in_hand:
            self.turn_index = (self.turn_index + 1) % n
            if self.turn_index == start:
                break

    def advance_round(self):
        print("ADVANCE ROUND CALLED FROM", self.round)
        self.players_to_act = {p.sid for p in self.in_hand}


        self.current_bet = 0
        self.bets = {p.sid: 0 for p in self.players}

        if self.round == "preflop":
            self.round = "flop"
        elif self.round == "flop":
            self.round = "turn"
        elif self.round == "turn":
            self.round = "river"
        elif self.round == "river":
            self.round = "done"
            return
        self.turn_index = self.small_blind_index
        self._skip_to_next_active()




    def betting_round_complete(self):
        return len(self.players_to_act) == 0
    
    def is_hand_over(self):
        """Check if hand is over (only 1 player left or reached showdown)"""
        return len(self.in_hand) <= 1 or self.round == "done"
    
    def award_pot_to_winner(self):
        """Award pot to the last remaining player"""
        if len(self.in_hand) == 1:
            winner = self.in_hand[0]
            winner.chips += self.pot
            print(f"{winner.name} wins {self.pot} chips!")
            self.pot = 0
            return winner
        return None


    def add_player(self, player):
        if len(self.players) > 10:
            return False # Max 10 players
        self.players.append(player)
        return True
    
    def start_hand(self):
        self.in_hand = self.players.copy()
        self.players_to_act = {p.sid for p in self.in_hand}

        n = len(self.players)
        if n < 2:
            return

        self.round = "preflop"
        self.pot = 0
        self.current_bet = 0
        self.in_hand = self.players.copy()
        self.bets = {p.sid: 0 for p in self.players}

        self.small_blind_index %= n
        self.big_blind_index = (self.small_blind_index + 1) % n

        # ✅ PRE-FLOP: player AFTER big blind
        self.turn_index = (self.big_blind_index + 1) % n

        
    
    def place_bet(self, player_sid, amount):
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
    
        
    def get_current_player(self):
        if self.round == "done" or not self.players:
            return None

        self._skip_to_next_active()
        return self.players[self.turn_index]

        
    def advance_turn(self):
        n = len(self.players)
        if n == 0:
            return

        self.turn_index = (self.turn_index + 1) % n
        self._skip_to_next_active()
        
    def fold_current_player(self):
        player = self.get_current_player()
        if not player:
            return

        # Remove from hand
        self.in_hand = [p for p in self.in_hand if p.sid != player.sid]

        # Remove betting state
        self.players_to_act.discard(player.sid)
        self.bets.pop(player.sid, None)

    
    def can_check(self, player_sid):
        return self.current_bet == self.bets[player_sid]

    def call(self, player_sid):
        player = next(p for p in self.players if p.sid == player_sid)
        call_amount = self.current_bet - self.bets[player_sid]

        if call_amount <= 0:
            return True  # already matched

        if call_amount > player.chips:
            call_amount = player.chips  # all-in (simplified)

        player.chips -= call_amount
        self.pot += call_amount
        self.bets[player_sid] += call_amount
        return True
    
    def raise_bet(self, player_sid, raise_amount):
        player = next(p for p in self.players if p.sid == player_sid)

        call_amount = self.current_bet - self.bets[player_sid]
        total_needed = call_amount + raise_amount

        if total_needed > player.chips:
            return False

        player.chips -= total_needed
        self.pot += total_needed
        self.bets[player_sid] += total_needed
        self.current_bet += raise_amount
        return True


    def serialize(self):
        current = self.get_current_player()
        call_amount = 0
        if current:
            call_amount = self.current_bet - self.bets.get(current.sid, 0)

        return {
            "code": self.code,
            "players": [p.serialize() for p in self.players],
            "current_turn": self.get_current_player().name if self.get_current_player() else None,
            "pot": self.pot,
            "dealer": self.players[self.dealer_index].name if self.players else None,
            "community_cards": self.community_cards,
            "call_amount": call_amount,
            "round": self.round
        }