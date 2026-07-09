import {
  CheckCircle2,
  MessageSquare,
  Search,
  ShieldCheck,
  Sparkles,
} from "lucide-react"

import FeatureCard from "../components/FeatureCard"


export default function AuthPage({
  authMode,
  setAuthMode,
  form,
  setForm,
  error,
  isLoading,
  onSubmit,
}) {
  const isSignup = authMode === "signup"

  return (
    <main className="min-h-screen min-h-[100svh] bg-[#f7f5ef] text-slate-950">
      <section className="mx-auto grid min-h-screen min-h-[100svh] max-w-6xl items-center gap-6 px-4 py-6 sm:gap-8 sm:px-6 sm:py-8 lg:grid-cols-[minmax(0,1fr)_420px]">
        <div className="max-w-2xl">
          <div className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-white px-3 py-1 text-sm font-semibold text-emerald-700 shadow-sm">
            <Sparkles className="h-4 w-4" />
            Research Assistant
          </div>
          <h1 className="mt-5 text-3xl font-semibold tracking-normal sm:text-5xl">
            Sign in before you research.
          </h1>
          <p className="mt-4 max-w-xl text-sm leading-6 text-slate-600 sm:text-base sm:leading-7">
            Your focused workspace for quick answers, source-backed research, and clean summaries.
          </p>

          <div className="mt-6 grid gap-3 sm:mt-8 sm:grid-cols-2">
            <FeatureCard icon={ShieldCheck} text="Secure sign in" />
            <FeatureCard icon={CheckCircle2} text="1 research daily" />
            <FeatureCard icon={MessageSquare} text="10 chats daily" />
            <FeatureCard icon={Search} text="Web-backed research mode" />
          </div>
        </div>

        <form onSubmit={onSubmit} className="w-full rounded-lg border border-slate-200 bg-white p-4 shadow-panel sm:p-6">
          <div className="mb-6 inline-flex w-full rounded-lg border border-slate-200 bg-slate-50 p-1">
            <button
              type="button"
              className={`auth-tab ${!isSignup ? "auth-tab-active" : ""}`}
              onClick={() => setAuthMode("signin")}
            >
              Sign in
            </button>
            <button
              type="button"
              className={`auth-tab ${isSignup ? "auth-tab-active" : ""}`}
              onClick={() => setAuthMode("signup")}
            >
              Sign up
            </button>
          </div>

          <label className="field-label" htmlFor="username">
            User ID
          </label>
          <input
            id="username"
            className="field-input"
            value={form.username}
            onChange={(event) => setForm({ ...form, username: event.target.value })}
            autoComplete="username"
            placeholder={isSignup ? "Choose a unique user ID" : "Enter your user ID"}
            maxLength={30}
            pattern={isSignup ? "[A-Za-z0-9_.-]{3,30}" : undefined}
            title="Use 3-30 letters, numbers, dot, dash, or underscore."
            required
          />

          {isSignup && (
            <>
              <label className="field-label" htmlFor="email">
                Email
              </label>
              <input
                id="email"
                className="field-input"
                value={form.email}
                onChange={(event) => setForm({ ...form, email: event.target.value })}
                type="email"
                autoComplete="email"
              />
            </>
          )}

          <label className="field-label" htmlFor="password">
            Password
          </label>
          <input
            id="password"
            className="field-input"
            value={form.password}
            onChange={(event) => setForm({ ...form, password: event.target.value })}
            type="password"
            autoComplete={isSignup ? "new-password" : "current-password"}
            minLength={isSignup ? 8 : undefined}
            required
          />

          {error && <div className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}

          <button
            type="submit"
            disabled={isLoading}
            className="mt-5 inline-flex min-h-[46px] w-full items-center justify-center rounded-lg bg-slate-950 px-4 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            {isLoading ? "Please wait..." : isSignup ? "Create account" : "Sign in"}
          </button>
        </form>
      </section>
    </main>
  )
}
