// src/components/3d/darkenColor.js

export function darkenColor(hex, factor = 0.7) {
  const f = parseInt(hex.slice(1), 16)
  const r = Math.floor((f >> 16) * factor)
  const g = Math.floor(((f >> 8) & 0x00ff) * factor)
  const b = Math.floor((f & 0x0000ff) * factor)
  return `rgb(${r}, ${g}, ${b})`
}
