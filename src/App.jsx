import { useEffect, useState } from "react"

import { apiRequest } from "./lib/api"
import { cleanBadUrl, clearToken, getStoredToken, storeToken } from "./lib/storage"
import AssistantPage from "./pages/AssistantPage"
import AuthPage from "./pages/AuthPage"
import ProfilePage from "./pages/ProfilePage"


export default function App() {
  const [authMode, setAuthMode] = useState("signin")
  const [token, setToken] = useState(() => getStoredToken())
  const [user, setUser] = useState(null)
  const [authForm, setAuthForm] = useState({ username: "", email: "", password: "" })
  const [authError, setAuthError] = useState("")
  const [authLoading, setAuthLoading] = useState(false)
  const [page, setPage] = useState("assistant")
  const [conversation, setConversation] = useState(null)

  useEffect(() => {
    cleanBadUrl()
  }, [])

  useEffect(() => {
    if (!token) return
    apiRequest("/api/auth/me/")
      .then((data) => setUser(data.user))
      .catch(() => {
        clearToken()
        setToken(null)
        setConversation(null)
      })
  }, [token])

  async function submitAuth(event) {
    event.preventDefault()
    setAuthError("")
    setAuthLoading(true)

    try {
      const path = authMode === "signup" ? "/api/auth/signup/" : "/api/auth/login/"
      const payload =
        authMode === "signup"
          ? authForm
          : { username: authForm.username, password: authForm.password }
      const data = await apiRequest(path, {
        method: "POST",
        body: JSON.stringify(payload),
      })

      storeToken(data.token)
      setToken(data.token)
      setUser(data.user)
      setConversation(null)
      setPage("assistant")
    } catch (error) {
      setAuthError(error.message)
    } finally {
      setAuthLoading(false)
    }
  }

  async function logout() {
    try {
      await apiRequest("/api/auth/logout/", { method: "POST", body: "{}" })
    } catch {
      // Logging out locally still gives the user the expected result.
    }
    clearToken()
    setToken(null)
    setUser(null)
    setConversation(null)
    setPage("assistant")
  }

  function refreshSession(data) {
    if (data.token) {
      storeToken(data.token)
      setToken(data.token)
    }
    if (data.user) {
      setUser(data.user)
    }
  }

  if (!token || !user) {
    return (
      <AuthPage
        authMode={authMode}
        setAuthMode={setAuthMode}
        form={authForm}
        setForm={setAuthForm}
        error={authError}
        isLoading={authLoading}
        onSubmit={submitAuth}
      />
    )
  }

  if (page === "profile") {
    return (
      <ProfilePage
        user={user}
        onBack={() => setPage("assistant")}
        onLogout={logout}
        onSessionRefresh={refreshSession}
      />
    )
  }

  return (
    <AssistantPage
      user={user}
      conversation={conversation}
      setConversation={setConversation}
      onProfileClick={() => setPage("profile")}
    />
  )
}
