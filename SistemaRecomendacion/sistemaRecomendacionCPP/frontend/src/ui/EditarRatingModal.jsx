// src/components/ui/EditarRatingModal.jsx
import React, { useState } from 'react'
import './EditarRatingModal.css'

const EditarRatingModal = ({ pelicula, userId, onClose, onSave }) => {
  const [nuevoRating, setNuevoRating] = useState(pelicula.rating)

  const guardar = async () => {
    try {
      const res = await fetch('http://localhost:8080/api/calificar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          movie_id: pelicula.movie_id,
          rating: nuevoRating
        })
      })
      if (res.ok) onSave(nuevoRating)
    } catch (err) {
      console.error('Error al guardar rating:', err)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h3>{pelicula.title}</h3>
        <div className="star-selector">
          {[1, 2, 3, 4, 5].map(i => (
            <span
              key={i}
              className={nuevoRating >= i ? 'star full' : nuevoRating >= i - 0.5 ? 'star half' : 'star empty'}
              onClick={() => setNuevoRating(i)}
            >★</span>
          ))}
        </div>
        <div className="modal-buttons">
          <button onClick={guardar}>Guardar</button>
          <button onClick={onClose}>Cancelar</button>
        </div>
      </div>
    </div>
  )
}

export default EditarRatingModal
