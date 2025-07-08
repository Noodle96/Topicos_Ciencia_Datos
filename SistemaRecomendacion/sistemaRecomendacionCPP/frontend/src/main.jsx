import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './style.css'
import LoginPage from './pages/LoginPage.jsx'


createRoot(document.getElementById('root')).render(
  <StrictMode>
    <LoginPage />
  </StrictMode>,
)
