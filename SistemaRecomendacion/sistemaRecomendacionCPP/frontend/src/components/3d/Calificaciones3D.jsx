// src/components/3d/Calificaciones3D.jsx
import React, { useEffect, useState } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Stars, Html } from '@react-three/drei'
import { useUser } from '../../context/UserContext'
import { darkenColor } from './darkenColor'

function getSpacedCoordinatesInGenreBand(
  indexInGenre,
  totalInGenre,
  phiStart,
  phiLength,
  radius = 3.3
) {
  const phi = phiStart + ((indexInGenre + 0.5) / totalInGenre) * phiLength
  const theta = (indexInGenre / totalInGenre) * 2 * Math.PI
  const x = radius * Math.sin(phi) * Math.cos(theta)
  const y = radius * Math.cos(phi)
  const z = radius * Math.sin(phi) * Math.sin(theta)
  return [x, y, z]
}

const Calificaciones3D = () => {
  const { userId } = useUser()
  const [peliculas, setPeliculas] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [hovered, setHovered] = useState(null)
  const radius = 3

  useEffect(() => {
    if (!userId) return
    setLoading(true)
    fetch(`http://localhost:8080/api/user_ratings?user_id=${userId}`)
      .then((res) => {
        if (!res.ok) throw new Error('Error al obtener datos')
        return res.json()
      })
      .then((data) => {
        setPeliculas(data)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }, [userId])

  if (loading) return <p>Cargando datos del usuario...</p>
  if (error) return <p>Error: {error}</p>
  if (!peliculas.length) return <p>No se encontraron calificaciones.</p>

  const generosImportantes = Array.from(
    new Set(peliculas.flatMap((p) => p.genres))
  ).filter((g) => g)

  const generoColores = {
    "Film-Noir": "#636e72",
    "Musical": "#fd79a8",
    "Documentary": "#00b894",
    "Adventure": "#fab1a0",
    "War": "#6c5ce7",
    "Animation": "#ffeaa7",
    "Children": "#55efc4",
    "Western": "#e17055",
    "Comedy": "#fdcb6e",
    "Romance": "#e84393",
    "IMAX": "#00cec9",
    "Fantasy": "#a29bfe",
    "Mystery": "#b2bec3",
    "Action": "#d63031",
    "(no genres listed)": "#b2bec3",
    "Drama": "#2d3436",
    "Thriller": "#0984e3",
    "Crime": "#e17055",
    "Horror": "#2c3e50",
    "Sci-Fi": "#74b9ff"
  }

  const peliculasPorGenero = {}
  peliculas.forEach((p) => {
    p.genres.forEach((genero) => {
      if (!generosImportantes.includes(genero)) return
      if (!peliculasPorGenero[genero]) peliculasPorGenero[genero] = []
      peliculasPorGenero[genero].push(p)
    })
  })

  const totalPeliculas = Object.values(peliculasPorGenero).reduce(
    (sum, lista) => sum + lista.length, 0
  )

  const proporcionesPorGenero = generosImportantes.map((genero) => ({
    genero,
    cantidad: peliculasPorGenero[genero]?.length || 0,
    proporcion: (peliculasPorGenero[genero]?.length || 0) / totalPeliculas
  }))

  const phiPorGenero = {}
  let phiCursor = 0
  proporcionesPorGenero.forEach(({ genero, proporcion }) => {
    const phiLength = proporcion * Math.PI
    phiPorGenero[genero] = { phiStart: phiCursor, phiLength }
    phiCursor += phiLength
  })

  return (
    <div style={{ display: 'flex', flexDirection: 'row', gap: '2rem' }}>
      <div style={{ width: '75%', height: '550px' }}>
        <Canvas>
          <ambientLight intensity={0.5} />
          <pointLight position={[10, 10, 10]} />

          {proporcionesPorGenero.map(({ genero }) => {
            const color = generoColores[genero] || '#cccccc'
            const { phiStart, phiLength } = phiPorGenero[genero]
            return (
              <mesh key={genero}>
                <sphereGeometry args={[radius, 64, 64, 0, 2 * Math.PI, phiStart, phiLength]} />
                <meshStandardMaterial color={color} />
              </mesh>
            )
          })}

          {Object.entries(peliculasPorGenero).flatMap(([genero, lista]) =>
            lista.map((pelicula, idx) => {
              const { phiStart, phiLength } = phiPorGenero[genero]
              const [x, y, z] = getSpacedCoordinatesInGenreBand(idx, lista.length, phiStart, phiLength, radius + 0.3)
              const pointColor = darkenColor(generoColores[genero] || '#999')
              return (
                <group key={`${pelicula.movie_id}-${genero}`}>
                  <mesh position={[x, y, z]}>
                    <sphereGeometry args={[0.09, 16, 16]} />
                    <meshStandardMaterial color="white" transparent opacity={0.3} />
                  </mesh>
                  <mesh
                    position={[x, y, z]}
                    onPointerOver={() => setHovered(`${pelicula.movie_id}-${genero}`)}
                    onPointerOut={() => setHovered(null)}
                  >
                    <sphereGeometry args={[0.06, 16, 16]} />
                    <meshStandardMaterial color={pointColor} />
                    {hovered === `${pelicula.movie_id}-${genero}` && (
                      <Html distanceFactor={10}>
                        <div style={{ background: '#fff', borderRadius: '8px', padding: '0.5rem', fontSize: '0.85rem', textAlign: 'center', boxShadow: '0 0 4px rgba(0,0,0,0.2)' }}>
                          <strong>{pelicula.title}</strong>
                          <div style={{ margin: '0.3rem 0' }}>
                            {"★".repeat(Math.floor(pelicula.rating))}
                            <span style={{ color: '#ccc' }}>{"★".repeat(5 - Math.floor(pelicula.rating))}</span>
                          </div>
                          <div style={{ fontSize: '0.75rem', color: '#777' }}>
                            Rating: {pelicula.rating.toFixed(1)}
                          </div>
                        </div>
                      </Html>
                    )}
                  </mesh>
                </group>
              )
            })
          )}

          <Stars radius={10} depth={50} count={5000} factor={4} fade />
          <OrbitControls enableZoom={false} />
        </Canvas>
      </div>

      <div style={{ width: '25%', paddingTop: '1rem' }}>
        <h4>Géneros por color</h4>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {proporcionesPorGenero.map(({ genero, cantidad }) => (
            <div key={genero} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <div style={{ width: '16px', height: '16px', backgroundColor: generoColores[genero] || '#ccc', borderRadius: '50%' }} />
              <span style={{ fontSize: '0.9rem' }}>{genero} ({cantidad})</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default Calificaciones3D
