import { useEffect, useState } from "react"

import { apiRequest } from "./lib/api"
import { cleanBadUrl, clearToken, getStoredToken, getStoredUser, initDeviceFingerprint, storeToken, storeUser } from "./lib/storage"
import AssistantPage from "./pages/AssistantPage"
import AuthPage from "./pages/AuthPage"
import ProfilePage from "./pages/ProfilePage"


export default function App() {
  const [pathname, setPathname] = useState(() => window.location.pathname)
  const [token, setToken] = useState(() => getStoredToken())
  const [user, setUser] = useState(() => getStoredUser())
  const [authForm, setAuthForm] = useState({ username: "", email: "", password: "" })
  const [authError, setAuthError] = useState("")
  const [authLoading, setAuthLoading] = useState(false)
  const [conversation, setConversation] = useState(null)

  const authMode = pathname === "/signup" ? "signup" : "signin"

  function navigateTo(path) {
    window.history.pushState({}, "", path)
    setPathname(path)
  }

  useEffect(() => {
    cleanBadUrl()
    initDeviceFingerprint()

    const handlePopState = () => {
      setPathname(window.location.pathname)
    }
    window.addEventListener("popstate", handlePopState)
    return () => window.removeEventListener("popstate", handlePopState)
  }, [])

  // Handle URL-based route redirection/guards based on auth status
  useEffect(() => {
    if (!token || !user) {
      if (pathname !== "/signup" && pathname !== "/signin" && pathname !== "/login") {
        navigateTo("/signin")
      }
    } else {
      if (pathname === "/signup" || pathname === "/signin" || pathname === "/login") {
        navigateTo("/")
      } else if (pathname !== "/" && pathname !== "/profile") {
        navigateTo("/")
      }
    }
  }, [token, user, pathname])

  // Silently verify the cached session in the background
  useEffect(() => {
    if (!token) return
    apiRequest("/api/auth/me/")
      .then((data) => {
        setUser(data.user)
        storeUser(data.user)
      })
      .catch(() => {
        clearToken()
        setToken(null)
        setUser(null)
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
      storeUser(data.user)
      setConversation(null)
      navigateTo("/")
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
    navigateTo("/signin")
  }

  function refreshSession(data) {
    if (data.token) {
      storeToken(data.token)
      setToken(data.token)
    }
    if (data.user) {
      setUser(data.user)
      storeUser(data.user)
    }
  }

  if (!token || !user) {
    return (
      <AuthPage
        authMode={authMode}
        setAuthMode={(mode) => navigateTo(mode === "signup" ? "/signup" : "/signin")}
        form={authForm}
        setForm={setAuthForm}
        error={authError}
        isLoading={authLoading}
        onSubmit={submitAuth}
      />
    )
  }

  if (pathname === "/profile") {
    return (
      <ProfilePage
        user={user}
        onBack={() => navigateTo("/")}
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
      onProfileClick={() => navigateTo("/profile")}
    />
  )
}
