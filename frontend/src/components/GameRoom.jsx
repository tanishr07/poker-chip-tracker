import { useState, useEffect } from 'react'
import '../styles/GameRoom.css'
import PlayerList from './PlayerList'
import GameInfo from './GameInfo'
import ActionLog from './ActionLog'
import ActionButtons from './ActionButtons'
import GameConfig from './GameConfig'

export default function GameRoom({ socket, roomCode, gameState, playerName, onLeave }) {
  const [actions, setActions] = useState([])
  const [isLeader, setIsLeader] = useState(false)
  const [showMessage, setShowMessage] = useState(false)
  const [showSettingsModal, setShowSettingsModal] = useState(false)

  useEffect(() => {
    if (!socket) return

    socket.on('action_log', (data) => {
      setActions(prev => [...prev, data.message])
    })

    socket.on('hand_over', (data) => {
      setActions(prev => [...prev, `💰 ${data.winner} wins $${data.pot.toFixed(2)}!`])
    })

    return () => {
      socket.off('action_log')
      socket.off('hand_over')
    }
  }, [socket])

  useEffect(() => {
    if (gameState && socket) {
      setIsLeader(socket.id === gameState.leader_sid)
    }
  }, [gameState, socket])

  if (!gameState) {
    return (
      <div className="game-loading">
        <div className="spinner"></div>
        <p>Loading game...</p>
      </div>
    )
  }

  return (
    <div className="game-container">
      <div className="game-main poker-table">
        <div className="game-header">
          <h1>Poker Chip Tracker</h1>
          <div className="room-info">
            <span onClick={() => {navigator.clipboard.writeText(roomCode); setShowMessage(true); setTimeout(() => setShowMessage(false), 2000);}} className="room-code">Room: {roomCode}</span>
            {showMessage && <span className="temp-message">Copied!</span>}
            {isLeader && (
                <button className="card-glass-button" onClick={() => setShowSettingsModal(true)}>Open Settings</button>
            )}
            <button className="card-glass-button leave-btn" onClick={onLeave}>Leave</button>
          </div>
        </div>

        <GameInfo gameState={gameState} playerName={playerName} />

        <div className="game-content">
          <div className="left-panel">
            <PlayerList gameState={gameState} currentPlayer={playerName} />
          </div>

          <div className="center-panel">
            <ActionButtons socket={socket} roomCode={roomCode} gameState={gameState} playerName={playerName} isLeader={isLeader} />
            {isLeader && !gameState?.hand_started && <GameConfig socket={socket} roomCode={roomCode} gameState={gameState} />}
          </div>

          <div className="right-panel">
            <ActionLog actions={actions} />
          </div>
        </div>
      </div>
      {showSettingsModal && (
              <div className="modal-overlay" onClick={() => setShowSettingsModal(false)}>
                <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                  <GameConfig socket={socket} roomCode={roomCode} gameState={gameState} />
                  <button className="card-glass-button close-btn" onClick={() => setShowSettingsModal(false)}>Close</button>
                </div>
              </div>
            )}
    </div>
  )
}
