// // src/components/calificar/PeliculasPorGenero.jsx
// import React, { useEffect, useState } from 'react'
// import { useUser } from '../../context/UserContext'
// import PeliculaCard from '../../ui/PeliculaCard'
// import './PeliculasPorGenero.css'

// const PeliculasPorGenero = ({ genero }) => {
//   const { userId } = useUser()
//   const [peliculas, setPeliculas] = useState([])
//   const [loading, setLoading] = useState(false)

//   useEffect(() => {
//     if (!genero || !userId) return

//     const fetchPeliculas = async () => {
//       setLoading(true)
//       try {
//         const res = await fetch(`http://localhost:8080/api/peliculas_no_calificadas?user_id=${userId}&genre=${genero}`)
//         const data = await res.json()
//         setPeliculas(data)
//       } catch (err) {
//         console.error('Error al cargar películas por género:', err)
//       } finally {
//         setLoading(false)
//       }
//     }

//     fetchPeliculas()
//   }, [genero, userId])

//   return (
//     <div className="peliculas-genero-container">
//       <h3 className="peliculas-genero-titulo">Películas de {genero} que aún no has calificado</h3>
//       {loading ? (
//         <p className="peliculas-genero-loading">Cargando películas...</p>
//       ) : (
//         <div className="peliculas-genero-grid">
//           {peliculas.length > 0 ? (
//             peliculas.map(p => (
//               <PeliculaCard key={p.movie_id} pelicula={p} editable={true} />
//             ))
//           ) : (
//             <p className="peliculas-genero-vacio">No hay películas nuevas por calificar en este género.</p>
//           )}
//         </div>
//       )}
//     </div>
//   )
// }

// export default PeliculasPorGenero

import React, { useEffect, useState } from 'react'
import { useUser } from '../../context/UserContext'
import PeliculaCard from '../../ui/PeliculaCard'
import './PeliculasPorGenero.css'

const PeliculasPorGenero = ({ genero }) => {
  const { userId } = useUser()
  const [peliculas, setPeliculas] = useState([])
  const [loading, setLoading] = useState(false)
  const [pagina, setPagina] = useState(1)

  const peliculasPorPagina = 18
  const totalPaginas = Math.ceil(peliculas.length / peliculasPorPagina)

  useEffect(() => {
    if (!genero || !userId) return

    const fetchPeliculas = async () => {
      setLoading(true)
      try {
        const res = await fetch(`http://localhost:8080/api/peliculas_no_calificadas?user_id=${userId}&genre=${genero}`)
        const data = await res.json()
        setPeliculas(data)
        setPagina(1) // resetear a la primera página cuando cambia de género
      } catch (err) {
        console.error('Error al cargar películas por género:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchPeliculas()
  }, [genero, userId])

  const peliculasPagina = peliculas.slice(
    (pagina - 1) * peliculasPorPagina,
    pagina * peliculasPorPagina
  )

  return (
    <div className="peliculas-genero-container">
      <h3 className="peliculas-genero-titulo">Películas de {genero} que aún no has calificado</h3>
      {loading ? (
        <p className="peliculas-genero-loading">Cargando películas...</p>
      ) : (
        <>
          <div className="peliculas-genero-grid">
            {peliculasPagina.length > 0 ? (
              peliculasPagina.map(p => (
                <PeliculaCard key={p.movie_id} pelicula={p} editable={true} />
              ))
            ) : (
              <p className="peliculas-genero-vacio">No hay películas nuevas por calificar en este género.</p>
            )}
          </div>

          {/* 🔸 Paginación */}
          {totalPaginas > 1 && (
            <div className="paginacion">
              <button
                onClick={() => setPagina(p => p - 1)}
                disabled={pagina === 1}
              >
                ◀ Anterior
              </button>
              <span>Página {pagina} de {totalPaginas}</span>
              <button
                onClick={() => setPagina(p => p + 1)}
                disabled={pagina === totalPaginas}
              >
                Siguiente ▶
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default PeliculasPorGenero
