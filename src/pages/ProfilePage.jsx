import { useEffect, useState } from "react"
import { ArrowLeft, LogOut } from "lucide-react"

import BrandMark from "../components/BrandMark"
import Limit from "../components/Limit"
import ProfileCard from "../components/ProfileCard"
import { apiRequest } from "../lib/api"


export default function ProfilePage({ user, onBack, onLogout, onSessionRefresh }) {
  const [usage, setUsage] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    apiRequest("/api/usage/")
      .then((data) => setUsage(data.usage || null))
      .catch((requestError) => setError(requestError.message))
  }, [])

  return (
    <main className="min-h-screen min-h-[100svh] bg-[#f7f5ef] text-slate-950">
      <div className="mx-auto flex min-h-screen min-h-[100svh] w-full max-w-5xl flex-col px-3 py-3 sm:px-6 sm:py-5 lg:px-8">
        <header className="mb-4 flex flex-col gap-3 border-b border-slate-200 pb-4 sm:mb-5 sm:flex-row sm:items-center sm:justify-between">
          <div className="min-w-0">
            <BrandMark size="lg" />
            <p className="mt-2 text-sm font-medium text-slate-500">
              Profile
            </p>
          </div>

          <div className="grid w-full grid-cols-2 gap-2 sm:flex sm:w-auto sm:flex-row sm:items-center sm:gap-3">
            <button
              type="button"
              onClick={onBack}
              className="inline-flex min-h-[42px] items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50"
              title="Back"
            >
              <ArrowLeft className="h-4 w-4" />
              Back
            </button>
            <button
              type="button"
              onClick={onLogout}
              className="inline-flex min-h-[42px] items-center justify-center gap-2 rounded-lg border border-red-100 bg-red-50 px-3 text-sm font-semibold text-red-700 shadow-sm transition hover:bg-red-100"
              title="Log out"
            >
              <LogOut className="h-4 w-4" />
              Log out
            </button>
          </div>
        </header>

        <section className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px] lg:gap-5">
          <ProfileCard user={user} onSessionRefresh={onSessionRefresh} />

          <aside className="space-y-4">
            <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
              <h2 className="text-sm font-semibold uppercase tracking-normal text-slate-500">
                Daily limits
              </h2>
              <Limit
                label="Chat"
                used={usage?.chatUsed ?? 0}
                limit={user.isSuperuser ? null : usage?.chatLimit ?? 10}
              />
              <Limit
                label="Research"
                used={usage?.researchUsed ?? 0}
                limit={user.isSuperuser ? null : usage?.researchLimit ?? 1}
              />
              {error && (
                <div className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
                  {error}
                </div>
              )}
            </div>
          </aside>
        </section>
      </div>
    </main>
  )
}
