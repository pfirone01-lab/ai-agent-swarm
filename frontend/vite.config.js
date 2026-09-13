import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
// base must match your repo name for GitHub Pages project sites, e.g.
// https://<user>.github.io/ai-agent-swarm/ -> base: '/ai-agent-swarm/'
export default defineConfig({
  plugins: [react()],
  base: '/ai-agent-swarm/',
})
