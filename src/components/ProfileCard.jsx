import { useState } from "react"
import { KeyRound, UserRound } from "lucide-react"

import { apiRequest } from "../lib/api"


export default function ProfileCard({ user, onSessionRefresh }) {
  const [currentPassword, setCurrentPassword] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")
  const [isSaving, setIsSaving] = useState(false)

  async function handlePasswordChange(event) {
    event.preventDefault()
    setMessage("")
    setError("")
    setIsSaving(true)

    try {
      const data = await apiRequest("/api/auth/change-password/", {
        method: "POST",
        body: JSON.stringify({ currentPassword, newPassword }),
      })
      onSessionRefresh?.(data)
      setMessage(data.message || "Password updated.")
      setCurrentPassword("")
      setNewPassword("")
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-normal text-slate-500">
        <UserRound className="h-4 w-4 text-emerald-700" />
        Signed in account
      </div>
      <div className="mt-4 rounded-lg border border-slate-100 bg-slate-50 p-3">
        <div className="text-xs font-semibold uppercase tracking-normal text-slate-500">
          User ID
        </div>
        <div className="mt-1 text-sm font-semibold text-slate-900">{user.username}</div>
        <div className="mt-2 text-xs font-semibold uppercase tracking-normal text-slate-500">
          Email
        </div>
        <div className="mt-1 break-all text-sm text-slate-600">{user.email || "No email saved"}</div>
      </div>

      <form onSubmit={handlePasswordChange} className="mt-4">
        <div className="flex items-center gap-2 text-sm font-semibold text-slate-800">
          <KeyRound className="h-4 w-4 text-emerald-700" />
          Change password
        </div>
        <input
          className="mt-3 min-h-[44px] w-full rounded-lg border border-slate-300 px-3 text-base outline-none transition focus:border-emerald-600 focus:ring-4 focus:ring-emerald-100 sm:text-sm"
          type="password"
          value={currentPassword}
          onChange={(event) => setCurrentPassword(event.target.value)}
          placeholder="Current password"
          autoComplete="current-password"
          required
        />
        <input
          className="mt-2 min-h-[44px] w-full rounded-lg border border-slate-300 px-3 text-base outline-none transition focus:border-emerald-600 focus:ring-4 focus:ring-emerald-100 sm:text-sm"
          type="password"
          value={newPassword}
          onChange={(event) => setNewPassword(event.target.value)}
          placeholder="New password"
          autoComplete="new-password"
          minLength={8}
          required
        />
        {message && <div className="mt-3 rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{message}</div>}
        {error && <div className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}
        <button
          type="submit"
          disabled={isSaving}
          className="mt-3 inline-flex min-h-[40px] w-full items-center justify-center rounded-lg bg-slate-950 px-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {isSaving ? "Saving..." : "Update password"}
        </button>
      </form>
    </div>
  )
}
