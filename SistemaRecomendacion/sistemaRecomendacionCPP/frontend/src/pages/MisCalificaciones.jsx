// src/components/pages/MisCalificaciones.jsx
import React, { useEffect, useState } from 'react'
import { useUser } from '../context/UserContext'
import PeliculaCard from '../ui/PeliculaCard'
import './MisCalificaciones.css'

const MisCalificaciones = () => {
  const { userId } = useUser()
  const [peliculas, setPeliculas] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [pagina, setPagina] = useState(1)
  const porPagina = 18

  useEffect(() => {
    if (!userId) return
    setLoading(true)
    fetch(`http://localhost:8080/api/user_ratings?user_id=${userId}`)
      .then(res => res.json())
      .then(data => {
        setPeliculas(data)
        setLoading(false)
        setPagina(1)
      })
      .catch(err => {
        setError('Error al obtener películas')
        setLoading(false)
      })
  }, [userId])

  if (loading) return <p>Cargando...</p>
  if (error) return <p>{error}</p>

  const totalPaginas = Math.ceil(peliculas.length / porPagina)
  const inicio = (pagina - 1) * porPagina
  const peliculasPagina = peliculas.slice(inicio, inicio + porPagina)

  return (
    <div className="miscalificaciones-container">
      {/* <h2>Mis Calificaciones</h2> */}
      <p>Total de películas calificadas: {peliculas.length}</p>

      <div className="peliculas-grid">
        {peliculasPagina.map((p) => (
          <PeliculaCard key={p.movie_id} pelicula={p} />
        ))}
      </div>

      {totalPaginas > 1 && (
        <div className="paginacion">
          <button onClick={() => setPagina(p => Math.max(1, p - 1))} disabled={pagina === 1}>
            ◀ Anterior
          </button>
          <span>
            Página {pagina} de {totalPaginas}
          </span>
          <button onClick={() => setPagina(p => Math.min(totalPaginas, p + 1))} disabled={pagina === totalPaginas}>
            Siguiente ▶
          </button>
        </div>
      )}
    </div>
  )
}

export default MisCalificaciones
