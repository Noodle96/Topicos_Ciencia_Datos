// src/components/3d/genreUtils.js

export function getCoordinatesForGenre(index, total, radius = 2.1) {
  const goldenAngle = Math.PI * (3 - Math.sqrt(5)) // para distribución uniforme

  const theta = goldenAngle * index
  const y = 1 - (index / (total - 1)) * 2 // de 1 a -1
  const radiusAtY = Math.sqrt(1 - y * y) // círculo en ese "nivel"

  const x = Math.cos(theta) * radiusAtY
  const z = Math.sin(theta) * radiusAtY

  return [x * radius, y * radius, z * radius]
}
