import { useState, useEffect } from 'react'
import { io } from 'socket.io-client'
import './App.css'
import './styles/Components.css'
import GameLobby from './components/GameLobby'
import GameRoom from './components/GameRoom'

function App() {
  const [socket, setSocket] = useState(null)
  const [inRoom, setInRoom] = useState(false)
  const [roomCode, setRoomCode] = useState('')
  const [playerName, setPlayerName] = useState('')
  const [gameState, setGameState] = useState(null)

  useEffect(() => {
    // Connect to Flask backend
    const newSocket = io('http://localhost:5000')
    
    newSocket.on('connect', () => {
      console.log('Connected to server:', newSocket.id)
    })

    newSocket.on('room_created', (data) => {
      setRoomCode(data.code)
      setInRoom(true)
    })

    newSocket.on('room_update', (data) => {
      // Always accept server state; ensure we mark ourselves in-room and capture room code
      setInRoom(true)
      if (data?.code) {
        setRoomCode(data.code)
      }
      setGameState(data)
    })

    newSocket.on('join_error', (data) => {
      alert(data.message)
    })

    setSocket(newSocket)

    return () => {
      newSocket.close()
    }
  }, [])

  const handleCreateRoom = (name) => {
    setPlayerName(name)
    socket?.emit('create_room', { name })
  }

  const handleJoinRoom = (name, code) => {
    setPlayerName(name)
    setRoomCode(code)
    socket?.emit('join_room', { name, room: code })
    setInRoom(true)
  }

  const handleLeaveRoom = () => {
    socket?.emit('leave_room', { room: roomCode })
    setInRoom(false)
    setRoomCode('')
    setGameState(null)
  }

  if (!inRoom) {
    return <GameLobby onCreateRoom={handleCreateRoom} onJoinRoom={handleJoinRoom} />
  }

  return (
    <GameRoom 
      socket={socket} 
      roomCode={roomCode} 
      gameState={gameState} 
      playerName={playerName}
      onLeave={handleLeaveRoom}
    />
  )
}

export default App
