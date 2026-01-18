import { useState } from 'react'

export default function GameConfig({ socket, roomCode, gameState }) {
  const [startingChips, setStartingChips] = useState(gameState?.starting_chips || 10.00)
  const [smallBlind, setSmallBlind] = useState(gameState?.small_blind_amount || 0.10)
  const [bigBlind, setBigBlind] = useState(gameState?.big_blind_amount || 0.20)

  const handleConfigure = () => {
    socket?.emit('configure_game', {
      room: roomCode,
      starting_chips: startingChips,
      small_blind: smallBlind,
      big_blind: bigBlind,
    })
  }

  if (!gameState?.hand_started && gameState?.game_configured) {
    return null
  }

  return (
    <div className="game-config">
      <h3>⚙️ Game Settings</h3>
      <div className="config-input-group">
        <label>Starting Chips</label>
        <input
          type="number"
          step="0.01"
          min="1"
          value={startingChips}
          onChange={(e) => setStartingChips(parseFloat(e.target.value))}
        />
      </div>
      <div className="config-input-group">
        <label>Small Blind</label>
        <input
          type="number"
          step="0.01"
          min="0.01"
          value={smallBlind}
          onChange={(e) => setSmallBlind(parseFloat(e.target.value))}
        />
      </div>
      <div className="config-input-group">
        <label>Big Blind</label>
        <input
          type="number"
          step="0.01"
          min="0.01"
          value={bigBlind}
          onChange={(e) => setBigBlind(parseFloat(e.target.value))}
        />
      </div>
      <button className="btn-primary full-width" onClick={handleConfigure}>
        Apply Settings
      </button>
    </div>
  )
}
