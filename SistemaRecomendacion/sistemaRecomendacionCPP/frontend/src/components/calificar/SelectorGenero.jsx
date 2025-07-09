// src/components/calificar/SelectorGenero.jsx
import React from 'react'
import './SelectorGenero.css'

const generosDisponibles = [
  'Action', 'Adventure', 'Animation', 'Children', 'Comedy',
  'Crime', 'Documentary', 'Drama', 'Fantasy', 'Film-Noir',
  'Horror', 'IMAX', 'Musical', 'Mystery', 'Romance',
  'Sci-Fi', 'Thriller', 'War', 'Western'
]

const SelectorGenero = ({onSelect }) => {
  return (
    <div className="selector-genero">
      <h3>Selecciona un género para calificar nuevas películas</h3>
      <div className="generos-grid">
        {generosDisponibles.map((genero) => (
          <button
            key={genero}
            className="selector-genero-boton"
            onClick={() => onSelect(genero)} // ✅ aquí usamos onSelect
          >
            {genero}
          </button>
        ))}
      </div>
    </div>
  )
}

export default SelectorGenero
