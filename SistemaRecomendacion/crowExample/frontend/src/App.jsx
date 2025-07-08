import React, { useState } from 'react';

function App() {
  const [k, setK] = useState(3);
  const [vecinos, setVecinos] = useState([]);

  const obtenerVecinos = async () => {
    const res = await fetch(`http://localhost:8080/api/knn?k=${k}`);
    const data = await res.json();
    setVecinos(Object.values(data));
  };

  return (
    <div className="p-4">
      <h1 className="text-xl mb-2">Buscar vecinos</h1>
      <input
        type="number"
        value={k}
        onChange={(e) => setK(e.target.value)}
        className="border p-2 mr-2"
      />
      <button onClick={obtenerVecinos} className="bg-blue-500 text-white p-2">
        Obtener vecinos
      </button>

      <ul className="mt-4">
        {vecinos.map((v, i) => (
          <li key={i}>ID: {v.id}, Distancia: {v.distancia}</li>
        ))}
      </ul>
    </div>
  );
}

export default App;
