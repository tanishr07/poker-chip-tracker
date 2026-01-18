import { useState } from 'react'

export default function ActionButtons({ socket, roomCode, gameState, playerName, isLeader }) {
  const [raiseAmount, setRaiseAmount] = useState('')
  const [selectedWinner, setSelectedWinner] = useState('')

  const isMyTurn = playerName === gameState?.current_turn
  const canAct = isMyTurn && gameState?.hand_started

  const handleAction = (action) => {
    let amount = 0
    if (action === 'raise') {
      amount = parseFloat(raiseAmount) || 0
      setRaiseAmount('')
    }
    socket?.emit('action', { room: roomCode, action, amount })
  }

  const handleStartHand = () => {
    socket?.emit('start_hand', { code: roomCode })
  }

  const handleDeclareWinner = () => {
    if (!selectedWinner) {
      alert('Please select a winner')
      return
    }
    socket?.emit('declare_winner', { room: roomCode, winner: selectedWinner })
    setSelectedWinner('')
  }

  return (
    <div className="action-buttons-container">
      <h3>🎮 Game Controls</h3>

      {isLeader && !gameState?.hand_started && (
        <button className="btn-primary full-width" onClick={handleStartHand}>
          Start Hand
        </button>
      )}

      {canAct && (
        <div className="actions-group">
          <button
            className="btn-primary action-btn"
            disabled={!canAct}
            onClick={() => handleAction('fold')}
          >
            Fold
          </button>
          <button
            className="btn-primary action-btn"
            disabled={!canAct}
            onClick={() => handleAction('check')}
          >
            Check
          </button>
          <button
            className="btn-primary action-btn"
            disabled={!canAct || gameState?.call_amount === 0}
            onClick={() => handleAction('call')}
          >
            {gameState?.call_amount === 0 ? 'Check' : `Call $${gameState?.call_amount?.toFixed(2)}`}
          </button>
        </div>
      )}

      {canAct && (
        <div className="raise-group">
          <input
            type="number"
            step="0.01"
            min="0.01"
            placeholder="Raise amount"
            value={raiseAmount}
            onChange={(e) => setRaiseAmount(e.target.value)}
          />
          <button
            className="btn-primary raise-btn"
            disabled={!canAct || !raiseAmount}
            onClick={() => handleAction('raise')}
          >
            Raise
          </button>
        </div>
      )}

      {!canAct && gameState?.hand_started && (
        <div className="waiting-message">
          ⏳ Waiting for {gameState?.current_turn || 'next player'}...
        </div>
      )}

      {isLeader && gameState?.hand_started && (
        <div className="winner-selection">
          <h4>Declare Winner</h4>
          <select
            value={selectedWinner}
            onChange={(e) => setSelectedWinner(e.target.value)}
          >
            <option value="">Select Winner...</option>
            {gameState?.players?.map((p) => (
              <option key={p.name} value={p.name}>
                {p.name}
              </option>
            ))}
          </select>
          <button
            className="btn-primary full-width"
            disabled={!selectedWinner}
            onClick={handleDeclareWinner}
          >
            Award Pot
          </button>
        </div>
      )}
    </div>
  )
}
