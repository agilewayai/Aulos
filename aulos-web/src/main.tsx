import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { AssetUpdateToast } from './AssetUpdateToast.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
    <AssetUpdateToast />
  </StrictMode>,
)
