import React, { useState } from 'react'
import Modal from '../components/Modal'
import './LoginPage.css'

const LoginPage = () => {
  const [userId, setUserId] = useState('')
  const [modalMessage, setModalMessage] = useState(null)

  const crearNuevoUsuario = async () => {
    try {
      const res = await fetch('http://localhost:8080/api/add_user')
      const data = await res.json()
      const nuevoId = data.user_id
      setModalMessage(`Tu usuario ha sido creado exitosamente. Tu código es: ${nuevoId}`)
    } catch (err) {
      setModalMessage('Hubo un error al crear el usuario.')
    }
  }

  const verificarUsuario = async () => {
    if (!userId || isNaN(userId)) {
      setModalMessage('Por favor, ingresa un ID de usuario válido.')
      return
    }

    try {
      const res = await fetch(`http://localhost:8080/api/verify_user?user_id=${userId}`)
      const data = await res.json()
      if (data.exists) {
        // Usuario válido, redirigir o continuar
        console.log(`Usuario ${userId} verificado. Redirigiendo...`)
        // TODO: Aquí iría la navegación (React Router, Context, etc.)
        setModalMessage(`Bienvenido, usuario ${userId}.`)  // temporal
      } else {
        setModalMessage(`El usuario con ID ${userId} no existe. Intenta de nuevo.`)
      }
    } catch (err) {
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
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
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
