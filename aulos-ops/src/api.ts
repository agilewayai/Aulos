export type HealthResponse = {
  status: string
  service: string
  version: string
  backends?: Record<string, string>
}

export type ServiceCard = {
  id: string
  name: string
  role: string
  path: string
}

export const AULOS_SERVICES: ServiceCard[] = [
  { id: 'aulos-web', name: 'Web', role: 'Operator GUI', path: 'aulos-web/' },
  { id: 'aulos-api', name: 'API', role: 'HTTP gateway', path: 'aulos-api/' },
  { id: 'aulos-agent', name: 'Agent', role: 'LangGraph runtime', path: 'aulos-agent/' },
  { id: 'aulos-mcp', name: 'MCP', role: 'Agent integrations', path: 'aulos-mcp/' },
  { id: 'aulos-skills', name: 'Skills', role: 'Main harness skills', path: 'aulos-skills/' },
  { id: 'aulos-ops', name: 'Ops', role: 'Admin portal', path: 'aulos-ops/' },
]

const apiBase = import.meta.env.VITE_AULOS_API_BASE ?? ''

export async function fetchGatewayHealth(): Promise<HealthResponse> {
  const response = await fetch(`${apiBase}/health`)
  if (!response.ok) {
    throw new Error(`Health check failed (${response.status})`)
  }
  return response.json() as Promise<HealthResponse>
}
