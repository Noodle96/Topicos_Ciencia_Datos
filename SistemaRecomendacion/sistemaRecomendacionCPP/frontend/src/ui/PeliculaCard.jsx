// src/components/ui/PeliculaCard.jsx
import React, { useState } from 'react'
import './PeliculaCard.css'
import EditarRatingModal from './EditarRatingModal'
import { useUser } from '../context/UserContext'

const PeliculaCard = ({ pelicula }) => {
  const { userId } = useUser()
  const [rating, setRating] = useState(pelicula.rating)
  const [mostrarModal, setMostrarModal] = useState(false)
  const [mensaje, setMensaje] = useState('')

  const renderStars = () => {
    const stars = []
    for (let i = 1; i <= 5; i++) {
      if (rating >= i) {
        stars.push(<span key={i} className="star full">★</span>)
      } else if (rating >= i - 0.5) {
        stars.push(<span key={i} className="star half">★</span>)
      } else {
        stars.push(<span key={i} className="star empty">★</span>)
      }
    }
    return stars
  }

  const mostrarNotificacion = (texto) => {
    setMensaje(texto)
    setTimeout(() => setMensaje(''), 3000)
  }

  return (
    <>
      <div className="pelicula-card" onClick={() => setMostrarModal(true)}>
        <h4 className="pelicula-titulo">{pelicula.title}</h4>
        <img
          src={`/posters/${1}.jpeg`}
        //   src={`/posters/${pelicula.movie_id}.jpg`}
          alt="poster"
          className="pelicula-imagen"
        //   onError={(e) => { e.target.src = 'https://via.placeholder.com/120x160' }}
        />
        <div className="pelicula-rating">
          {renderStars()}
        </div>
        <p className="pelicula-generos">{pelicula.genres.join(', ')}</p>
        {mensaje && <div className="mensaje-rating">{mensaje}</div>}
      </div>

      {mostrarModal && (
        <EditarRatingModal
          pelicula={{ ...pelicula, rating }}
          userId={userId}
          onClose={() => setMostrarModal(false)}
          onSave={(nuevo) => {
            setRating(nuevo)
            setMostrarModal(false)
            mostrarNotificacion('¡Rating actualizado!')
          }}
        />
      )}
    </>
  )
}

export default PeliculaCard
