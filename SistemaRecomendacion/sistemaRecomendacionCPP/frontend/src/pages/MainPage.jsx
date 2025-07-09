import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useUser } from '../context/UserContext'
import './MainPage.css'
import MisCalificaciones from './MisCalificaciones'
import CalificarNuevas from './CalificarNuevas'

const MainPage = () => {

  useEffect(() => {
    const beforeUnload = (e) => {
      e.preventDefault()
      e.returnValue = ''
    }
    window.addEventListener('beforeunload', beforeUnload)
    return () => window.removeEventListener('beforeunload', beforeUnload)
  }, [])


  const { userId, setUserId } = useUser()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('calificaciones')

  const cerrarSesion = () => {
    setUserId(null)
    navigate('/')
  }

  return (
    <div className="main-container">
        <div className="main-header redesigned">
            <div className="user-info">
                <span className="user-avatar">👤</span>
                <span className="user-id">Usuario # {userId}</span>
            </div>
            <button className="logout-button" onClick={cerrarSesion}> Cerrar sesión   </button>
        </div>

      <div className="tab-bar">
        <button
          className={activeTab === 'calificaciones' ? 'tab-button active' : 'tab-button'}
          onClick={() => setActiveTab('calificaciones')}
        >
          Mis Calificaciones
        </button>
        <button
          className={activeTab === 'recomendar' ? 'tab-button active' : 'tab-button'}
          onClick={() => setActiveTab('recomendar')}
        >
          Recomendaciones
        </button>
        <button
          className={activeTab === 'calificar' ? 'tab-button active' : 'tab-button'}
          onClick={() => setActiveTab('calificar')}
        >
          Calificar Nuevas
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'calificaciones' && (
          <div>
            {/* Aquí se mostrarán tus calificaciones */}
            {/* <Calificaciones3D /> */}
            <MisCalificaciones />
          </div>

        )}
        {activeTab === 'recomendar' && (
          <div>Aquí se mostrarán recomendaciones para ti</div>
        )}
        {activeTab === 'calificar' && (
          // <div>Aquí podrás calificar nuevas películas</div>
          <CalificarNuevas />
        )}
      </div>
    </div>
  )
}

export default MainPage
