// src/components/recomendar/Recomendaciones.jsx
import React, { useState } from 'react'
import { useUser } from '../../context/UserContext'
import PeliculaCard from '../../ui/PeliculaCard'
import './Recomendaciones.css'

const Recomendaciones = () => {
  const { userId } = useUser()
  const [peliculas, setPeliculas] = useState([])
  const [pagina, setPagina] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [mostradasPorPagina] = useState(20)

  const recomendar = async () => {
    if (!userId) return
    setLoading(true)
    setError('')
    try {
      const res = await fetch(`http://localhost:8080/api/recomendar?user_id=${userId}&n=100&metric=cosine`)
      if (!res.ok) throw new Error('Peliculas insuficientes para recomendar')
      const data = await res.json()
      setPeliculas(data)
      setPagina(1)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const inicio = (pagina - 1) * mostradasPorPagina
  const fin = inicio + mostradasPorPagina
  const peliculasPagina = peliculas.slice(inicio, fin)
  const totalPaginas = Math.ceil(peliculas.length / mostradasPorPagina)

  return (
    <div className="recomendaciones-container">
      <h3>Películas recomendadas para ti</h3>
      <button className="boton-recomendar" onClick={recomendar}>Recomiéndame</button>

      {loading && <p className="mensaje-cargando">Cargando recomendaciones...</p>}
      {error && <p className="mensaje-error">{error}</p>}

      {!loading && peliculas.length > 0 && (
        <>
          <div className="recomendaciones-grid">
            {peliculasPagina.map((p) => (
              <PeliculaCard key={p.movie_id} pelicula={p} editable={true} />
            ))}
          </div>

          <div className="recomendaciones-paginacion">
            <button onClick={() => setPagina(p => Math.max(p - 1, 1))} disabled={pagina === 1}>Anterior</button>
            <span>Página {pagina} de {totalPaginas}</span>
            <button onClick={() => setPagina(p => Math.min(p + 1, totalPaginas))} disabled={pagina === totalPaginas}>Siguiente</button>
          </div>
        </>
      )}
    </div>
  )
}

export default Recomendaciones
