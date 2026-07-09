import { Bot, User } from "lucide-react"

import MarkdownText from "./MarkdownText"


export default function Message({ item }) {
  const isUser = item.role === "user"

  return (
    <article className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && (
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-emerald-50 text-emerald-700">
          <Bot className="h-5 w-5" />
        </div>
      )}
      <div className={`max-w-full sm:max-w-[820px] ${isUser ? "message-user" : "message-assistant"}`}>
        {isUser ? (
          <div className="whitespace-pre-wrap text-sm leading-6">{item.content}</div>
        ) : (
          <MarkdownText content={item.content} />
        )}
        {item.email && (
          <div className="mt-3 text-xs font-medium text-slate-500">
            {item.email.sent ? "Email sent." : `Email failed: ${item.email.error}`}
          </div>
        )}
      </div>
      {isUser && (
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-900 text-white">
          <User className="h-5 w-5" />
        </div>
      )}
    </article>
  )
}
