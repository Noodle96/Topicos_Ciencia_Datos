// src/components/3d/getSpacedCoordinatesInGenreBand.js

export function getSpacedCoordinatesInGenreBand(
  genero,
  generos,
  indexInGenre,
  totalInGenre,
  radius = 3.3
) {
  const idx = generos.indexOf(genero)
  const total = generos.length

  const phiMin = (idx / total) * Math.PI
  const phiMax = ((idx + 1) / total) * Math.PI
  const phi = phiMin + ((indexInGenre + 0.5) / totalInGenre) * (phiMax - phiMin)

  const theta = (indexInGenre / totalInGenre) * 2 * Math.PI

  const x = radius * Math.sin(phi) * Math.cos(theta)
  const y = radius * Math.cos(phi)
  const z = radius * Math.sin(phi) * Math.sin(theta)

  return [x, y, z]
}
