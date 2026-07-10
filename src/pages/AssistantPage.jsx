import { useEffect, useMemo, useState } from "react"
import {
  Bot,
  Mail,
  MessageSquare,
  Search,
  Send,
  User,
} from "lucide-react"

import BrandMark from "../components/BrandMark"
import Message from "../components/Message"
import { apiRequest } from "../lib/api"


const initialConversation = [
  {
    role: "assistant",
    content: "Loid is ready. Start a chat or begin a Research query.",
    sources: [],
  },
]

const chatLoadingMessages = [
  "Thinking...",
  "Generating response...",
]

const missionLoadingMessages = [
  "Loid is searching for relevant intelligence sources...",
  "Loid is reading sources...",
  "Loid is analyzing intelligence...",
  "Loid is preparing the research brief...",
]


export default function AssistantPage({ user, conversation, setConversation, onProfileClick }) {
  const [mode, setMode] = useState("chat")
  const [message, setMessage] = useState("")
  const [sendEmail, setSendEmail] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [isHistoryLoading, setIsHistoryLoading] = useState(!conversation)
  const [loadingStatusIndex, setLoadingStatusIndex] = useState(0)
  const [error, setError] = useState("")
  const activeLoadingMessages = mode === "research" ? missionLoadingMessages : chatLoadingMessages

  const canSubmit = useMemo(
    () => message.trim() && !isLoading && !isHistoryLoading,
    [message, isLoading, isHistoryLoading],
  )

  useEffect(() => {
    let isCurrent = true

    if (conversation) {
      setIsHistoryLoading(false)
      return () => {
        isCurrent = false
      }
    }

    setIsHistoryLoading(true)
    apiRequest("/api/conversations/")
      .then((data) => {
        if (!isCurrent) return
        setConversation(data.messages?.length ? data.messages : initialConversation)
      })
      .catch(() => {
        if (!isCurrent) return
        // History is helpful, but the assistant can still run without it.
        setConversation(initialConversation)
      })
      .finally(() => {
        if (isCurrent) setIsHistoryLoading(false)
      })

    return () => {
      isCurrent = false
    }
  }, [conversation, setConversation, user.id])

  useEffect(() => {
    if (mode === "chat") {
      setSendEmail(false)
    }
  }, [mode])

  useEffect(() => {
    if (!isLoading) {
      setLoadingStatusIndex(0)
      return undefined
    }

    setLoadingStatusIndex(0)
    const timer = window.setInterval(() => {
      setLoadingStatusIndex((index) => (index + 1) % activeLoadingMessages.length)
    }, 1600)

    return () => window.clearInterval(timer)
  }, [activeLoadingMessages.length, isLoading, mode])

  async function handleSubmit(event) {
    event.preventDefault()
    if (!canSubmit) return

    const trimmedMessage = message.trim()
    setError("")
    setMessage("")
    setIsLoading(true)
    setConversation((items) => [...(items || []), { role: "user", content: trimmedMessage, sources: [] }])

    try {
      const data = await apiRequest("/api/chat/", {
        method: "POST",
        body: JSON.stringify({
          message: trimmedMessage,
          mode,
          emailResult: mode === "research" && sendEmail,
        }),
      })

      if (data.history?.length) {
        setConversation(data.history)
      } else {
        setConversation((items) => [
          ...items,
          {
            role: "assistant",
            content: data.answer,
            sources: data.sources || [],
            email: data.email,
          },
        ])
      }
    } catch (requestError) {
      if (requestError.status === 429) {
        setConversation((items) => [
          ...(items || []),
          {
            role: "assistant",
            content: requestError.message,
            sources: [],
          },
        ])
      } else {
        setError(requestError.message)
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="min-h-screen min-h-[100svh] bg-[#f7f5ef] text-slate-950">
      <div className="mx-auto flex h-screen min-h-[100svh] w-full max-w-7xl flex-col px-3 py-3 sm:px-6 sm:py-5 lg:px-8">
        <header className="mb-4 flex flex-col gap-3 border-b border-slate-200 pb-4 sm:mb-5 sm:flex-row sm:items-center sm:justify-between">
          <BrandMark size="lg" />

          <div className="flex w-full items-center gap-2 sm:w-auto sm:gap-3">
            <div className="inline-flex min-w-0 flex-1 rounded-lg border border-slate-200 bg-white p-1 shadow-sm sm:flex-none">
              <button
                className={`mode-button ${mode === "chat" ? "mode-button-active" : ""}`}
                type="button"
                onClick={() => setMode("chat")}
                title="Chat"
              >
                <MessageSquare className="h-4 w-4" />
                Chat
              </button>
              <button
                className={`mode-button ${mode === "research" ? "mode-button-active" : ""}`}
                type="button"
                onClick={() => setMode("research")}
                title="Research"
              >
                <Search className="h-4 w-4" />
                Research
              </button>
            </div>
            <button
              type="button"
              onClick={onProfileClick}
              className="inline-flex min-h-[42px] shrink-0 items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50"
              title="Profile"
            >
              <User className="h-4 w-4" />
              <span className="hidden sm:inline">Profile</span>
            </button>
          </div>
        </header>

        <section className="grid min-h-0 flex-1 gap-4">
          <div className="flex min-h-0 flex-col overflow-hidden rounded-lg border border-slate-200 bg-white shadow-panel">
            <div className="mobile-scroll flex-1 space-y-4 overflow-y-auto p-3 sm:p-6">
              {(conversation || []).map((item, index) => (
                <Message key={`${item.role}-${index}`} item={item} />
              ))}
              {isHistoryLoading && !conversation && (
                <div className="flex items-center gap-3 rounded-lg bg-slate-50 p-4 text-sm text-slate-600">
                  <Bot className="h-5 w-5 text-emerald-700" />
                  Loid is retrieving saved briefings...
                </div>
              )}
              {isLoading && (
                <div className="flex items-center gap-3 rounded-lg bg-slate-50 p-4 text-sm text-slate-600">
                  <Bot className="h-5 w-5 text-emerald-700" />
                  {activeLoadingMessages[loadingStatusIndex]}
                </div>
              )}
            </div>

            {error && (
              <div className="border-t border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700 sm:px-6">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="border-t border-slate-200 p-3 sm:p-5">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-stretch">
                <div className="relative flex-1">
                  <textarea
                    value={message}
                    onChange={(event) => setMessage(event.target.value)}
                    className="min-h-[84px] w-full resize-none rounded-lg border border-slate-300 bg-white px-4 py-3 pr-14 text-base outline-none transition focus:border-emerald-600 focus:ring-4 focus:ring-emerald-100 sm:min-h-[92px] sm:pr-4 sm:text-sm"
                    placeholder={
                      mode === "research"
                        ? "Enter a research topic..."
                        : "Type a message..."
                    }
                  />
                  <button
                    type="submit"
                    disabled={!canSubmit}
                    className="absolute right-3 top-[44%] inline-flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-lg bg-emerald-700 text-white transition hover:bg-emerald-800 disabled:cursor-not-allowed disabled:bg-slate-300 sm:hidden"
                    title="Send"
                  >
                    <Send className="h-4 w-4" />
                  </button>
                </div>
                <div className="flex flex-col gap-2 sm:w-[132px] sm:justify-end">
                  <label
                    className={`hidden min-h-[40px] items-center justify-between gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm font-semibold text-slate-700 sm:flex ${
                      mode === "research" && user.email ? "cursor-pointer" : "cursor-not-allowed opacity-60"
                    }`}
                    title={user.email ? `Sends Loid's brief to ${user.email}` : "No account email saved"}
                  >
                    <span className="flex items-center gap-2">
                      <Mail className="h-4 w-4 text-emerald-700" />
                      Brief
                    </span>
                    <input
                      type="checkbox"
                      checked={sendEmail}
                      onChange={(event) => setSendEmail(event.target.checked)}
                      disabled={mode !== "research" || !user.email}
                      className="h-4 w-4 accent-emerald-700"
                    />
                  </label>
                <button
                  type="submit"
                  disabled={!canSubmit}
                    className="hidden min-h-[48px] w-full items-center justify-center gap-2 rounded-lg bg-emerald-700 px-5 text-sm font-semibold text-white transition hover:bg-emerald-800 disabled:cursor-not-allowed disabled:bg-slate-300 sm:inline-flex"
                  title="Send"
                >
                  <Send className="h-4 w-4" />
                  Send
                </button>
                  <label
                    className={`inline-flex min-h-[48px] w-full items-center justify-center gap-2 rounded-lg border px-4 text-sm font-semibold shadow-sm transition sm:hidden ${
                      mode === "research" && user.email
                        ? sendEmail
                          ? "border-emerald-200 bg-emerald-50 text-emerald-800"
                          : "border-slate-200 bg-white text-slate-700"
                        : "cursor-not-allowed border-slate-200 bg-slate-100 text-slate-400"
                    }`}
                    title={user.email ? `Sends Loid's brief to ${user.email}` : "No account email saved"}
                  >
                    <Mail className="h-4 w-4" />
                    Email brief
                    <input
                      type="checkbox"
                      checked={sendEmail}
                      onChange={(event) => setSendEmail(event.target.checked)}
                      disabled={mode !== "research" || !user.email}
                      className="sr-only"
                    />
                  </label>
                </div>
              </div>
            </form>
          </div>
        </section>
      </div>
    </main>
  )
}
