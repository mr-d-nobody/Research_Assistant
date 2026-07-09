export const TOKEN_KEY = "research_assistant_token"
export const DEVICE_KEY = "research_assistant_device_id"


export function cleanBadUrl() {
  const path = window.location.pathname
  if (path.startsWith("/http://") || path.startsWith("/https://")) {
    window.history.replaceState({}, "", "/")
  }
}


export function getStoredToken() {
  return localStorage.getItem(TOKEN_KEY)
}


export function storeToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}


export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}


export function getDeviceId() {
  const existing = localStorage.getItem(DEVICE_KEY)
  if (existing) return existing

  const generated =
    crypto.randomUUID?.() || `device-${Date.now()}-${Math.random().toString(16).slice(2)}`
  localStorage.setItem(DEVICE_KEY, generated)
  return generated
}
