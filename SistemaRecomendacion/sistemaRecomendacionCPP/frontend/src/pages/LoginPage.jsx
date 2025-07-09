import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useUser } from '../context/UserContext'
import Modal from '../components/Modal'
import './LoginPage.css'

const LoginPage = () => {
  const [userIdInput, setUserIdInput] = useState('')
  const [modalMessage, setModalMessage] = useState(null)
  const navigate = useNavigate()
  const { setUserId } = useUser()

  const crearNuevoUsuario = async () => {
    try {
      const res = await fetch('http://localhost:8080/api/add_user')
      const data = await res.json()
      setModalMessage(`Tu usuario ha sido creado exitosamente. Tu código es: ${data.user_id}`)
    } catch {
      setModalMessage('Error al crear usuario.')
    }
  }

  const verificarUsuario = async () => {
    if (!userIdInput || isNaN(userIdInput)) {
      setModalMessage('Por favor, ingresa un ID de usuario válido.')
      return
    }

    try {
      const res = await fetch(`http://localhost:8080/api/verify_user?user_id=${userIdInput}`)
      const data = await res.json()
      if (data.exists) {
        setUserId(Number(userIdInput))
        navigate('/main')
      } else {
        setModalMessage(`El usuario con ID ${userIdInput} no existe.`)
      }
    } catch {
      setModalMessage('Error al verificar usuario.')
    }
  }

  return (
    <div className="login-container">
      <h1 className="login-title">Sistema de Recomendación</h1>

      <div className="login-card">
        <h2>Iniciar sesión</h2>
        <input
          type="text"
          placeholder="Código de usuario"
          className="login-input"
          value={userIdInput}
          onChange={(e) => setUserIdInput(e.target.value)}
        />
        <button className="login-button" onClick={verificarUsuario}>Ingresar</button>
      </div>

      <div style={{ marginTop: '2rem' }}>
        <button className="secondary-button" onClick={crearNuevoUsuario}>
          Crear nuevo usuario
        </button>
      </div>

      {modalMessage && (
        <Modal message={modalMessage} onClose={() => setModalMessage(null)} />
      )}
    </div>
  )
}

export default LoginPage
