export default function GameInfo({ gameState, playerName }) {
  const isMyTurn = playerName === gameState?.current_turn

  return (
    <div className="game-info-container">
      <div className="info-card pot-display">
        <span>💰 Pot</span>
        <div className="pot-amount">${gameState?.pot?.toFixed(2) || '0.00'}</div>
      </div>

      <div className="info-card">
        <div className="info-label">Round</div>
        <div className="info-value">{gameState?.round?.toUpperCase()}</div>
      </div>

      <div className="info-card">
        <div className="info-label">Dealer</div>
        <div className="info-value">{gameState?.dealer || 'None'}</div>
      </div>

      <div className={`info-card ${isMyTurn ? 'your-turn' : ''}`}>
        <div className="info-label">Current Turn</div>
        <div className="info-value">{isMyTurn ? '👈 YOU' : gameState?.current_turn || 'None'}</div>
      </div>
    </div>
  )
}
