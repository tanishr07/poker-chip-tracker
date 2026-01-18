export default function PlayerList({ gameState, currentPlayer }) {
  return (
    <div className="player-list-container">
      <h3>👥 Players</h3>
      <div className="player-list">
        {gameState?.players?.map((player) => (
          <div
            key={player.name}
            className={`player-card ${player.name === currentPlayer ? 'current' : ''} ${
              player.name === gameState.current_turn ? 'active-turn' : ''
            }`}
          >
            <div className="player-name">
              {player.name === currentPlayer && '👤 '}
              {player.name}
              {player.name === gameState.current_turn && ' 🔴'}
            </div>
            <div className="player-chips">${player.chips.toFixed(2)}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
