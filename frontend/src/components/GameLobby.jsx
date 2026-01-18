import { useState } from 'react'
import '../styles/Lobby.css'

export default function GameLobby({ onCreateRoom, onJoinRoom }) {
  const [name, setName] = useState('')
  const [roomCode, setRoomCode] = useState('')
  const [tab, setTab] = useState('create') // 'create' or 'join'

  const handleCreateClick = () => {
    if (!name.trim()) {
      alert('Please enter your name')
      return
    }
    onCreateRoom(name)
  }

  const handleJoinClick = () => {
    if (!name.trim() || !roomCode.trim()) {
      alert('Please enter both name and room code')
      return
    }
    onJoinRoom(name, roomCode)
  }

  return (
    <div className="lobby-container">
      <div className="lobby-card card-glass">
        <h1 className="lobby-title">🎰 Poker Chip Tracker</h1>
        <p className="lobby-subtitle">Multiplayer Poker | Real-time Tracking</p>

        <div className="input-group">
          <label htmlFor="playerName">Your Name</label>
          <input
            id="playerName"
            type="text"
            placeholder="Enter your name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && (tab === 'create' ? handleCreateClick() : handleJoinClick())}
          />
        </div>

        <div className="tabs">
          <button
            className={`tab-btn ${tab === 'create' ? 'active' : ''}`}
            onClick={() => setTab('create')}
          >
            Create Room
          </button>
          <button
            className={`tab-btn ${tab === 'join' ? 'active' : ''}`}
            onClick={() => setTab('join')}
          >
            Join Room
          </button>
        </div>

        {tab === 'create' ? (
          <div className="tab-content">
            <p className="tab-description">Create a new game and share the code with friends</p>
            <button className="btn-primary create-btn" onClick={handleCreateClick}>
              Create New Room
            </button>
          </div>
        ) : (
          <div className="tab-content">
            <div className="input-group">
              <label htmlFor="roomCode">Room Code</label>
              <input
                id="roomCode"
                type="text"
                placeholder="Enter room code"
                value={roomCode}
                onChange={(e) => setRoomCode(e.target.value.toUpperCase())}
                onKeyPress={(e) => e.key === 'Enter' && handleJoinClick()}
                maxLength="5"
              />
            </div>
            <button className="btn-primary join-btn" onClick={handleJoinClick}>
              Join Room
            </button>
          </div>
        )}
      </div>

      <div className="lobby-footer">
        <p>No database needed • Real-time updates • In-memory tracking</p>
      </div>
    </div>
  )
}
