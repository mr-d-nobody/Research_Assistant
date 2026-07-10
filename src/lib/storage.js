export const TOKEN_KEY = "research_assistant_token"
export const DEVICE_KEY = "research_assistant_device_id"
export const USER_KEY = "research_assistant_user"


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
  localStorage.removeItem(USER_KEY)
}


export function getStoredUser() {
  try {
    const raw = localStorage.getItem(USER_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}


export function storeUser(user) {
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}


export function getDeviceId() {
  return localStorage.getItem(DEVICE_KEY) || "pending"
}


export async function initDeviceFingerprint() {
  try {
    const FingerprintJS = await import("@fingerprintjs/fingerprintjs")
    const fp = await FingerprintJS.load()
    const result = await fp.get()
    localStorage.setItem(DEVICE_KEY, result.visitorId)
  } catch {
    // Fallback to random ID if fingerprinting fails
    if (!localStorage.getItem(DEVICE_KEY)) {
      const fallback =
        crypto.randomUUID?.() || `device-${Date.now()}-${Math.random().toString(16).slice(2)}`
      localStorage.setItem(DEVICE_KEY, fallback)
    }
  }
}
