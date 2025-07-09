// src/pages/CalificarNuevas.jsx
import React, { useState } from 'react'
import SelectorGenero from '../components/calificar/SelectorGenero'
import PeliculasPorGenero from '../components/calificar/PeliculasPorGenero'
import './CalificarNuevas.css'

const CalificarNuevas = () => {
    const [generoSeleccionado, setGeneroSeleccionado] = useState(null)
    return (
        <div className="calificar-nuevas-container">
        <div className="calificar-nuevas-selector">
            <SelectorGenero onSelect={setGeneroSeleccionado} />
        </div>

        {generoSeleccionado && (
            <PeliculasPorGenero genero={generoSeleccionado} />
        )}
        </div>
  )
}

export default CalificarNuevas
