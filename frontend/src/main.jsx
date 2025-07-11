import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// PostHog setup
import posthog from 'posthog-js'

posthog.init('phc_k06q9F9aDWJ5HZAe3l4Rxuc7iyDeHhhhNJQ102PF82X', {
  api_host: 'https://app.posthog.com',
  capture_pageview: true,
})

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
