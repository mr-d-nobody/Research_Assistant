import { getDeviceId, getStoredToken } from "./storage"


const API_BASE = import.meta.env.VITE_API_BASE_URL || ""


export async function apiRequest(path, options = {}) {
  const token = getStoredToken()
  const headers = {
    "Content-Type": "application/json",
    "X-Device-ID": getDeviceId(),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  }

  let response
  try {
    response = await fetch(`${API_BASE}${path}`, { ...options, headers })
  } catch {
    throw new Error("We couldn't connect right now. Please refresh and try again.")
  }

  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    const error = new Error(data.error || "Request failed.")
    error.status = response.status
    error.data = data
    throw error
  }

  return data
}
