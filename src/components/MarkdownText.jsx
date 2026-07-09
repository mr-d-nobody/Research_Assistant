function renderInline(text) {
  const parts = []
  const pattern = /(\*\*([^*]+)\*\*|\[([^\]]+)\]\((https?:\/\/[^\s]+)\)|(https?:\/\/[^\s]+)|\*([^*]+)\*)/g
  let lastIndex = 0
  let match

  while ((match = pattern.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index))
    }

    if (match[2]) {
      parts.push(
        <strong key={parts.length} className="font-semibold text-slate-950">
          {match[2]}
        </strong>
      )
    } else if (match[3] && match[4]) {
      parts.push(
        <a
          key={parts.length}
          href={match[4]}
          target="_blank"
          rel="noreferrer"
          className="text-emerald-700 underline-offset-4 hover:underline"
        >
          {match[3]}
        </a>
      )
    } else if (match[5]) {
      parts.push(
        <a
          key={parts.length}
          href={match[5]}
          target="_blank"
          rel="noreferrer"
          className="break-all text-emerald-700 underline-offset-4 hover:underline"
        >
          {match[5]}
        </a>
      )
    } else if (match[6]) {
      parts.push(
        <em key={parts.length} className="italic">
          {match[6]}
        </em>
      )
    }

    lastIndex = pattern.lastIndex
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex))
  }

  return parts
}


function isBoldHeading(line) {
  return /^\*\*[^*]+:?\*\*$/.test(line.trim())
}


export default function MarkdownText({ content }) {
  const lines = String(content || "").split(/\r?\n/)
  const blocks = []
  let bullets = []

  function flushBullets() {
    if (!bullets.length) return

    blocks.push(
      <ul key={`ul-${blocks.length}`} className="my-3 list-disc space-y-1 pl-5">
        {bullets.map((bullet, index) => (
          <li key={`${bullet}-${index}`}>{renderInline(bullet)}</li>
        ))}
      </ul>
    )
    bullets = []
  }

  lines.forEach((line, index) => {
    const trimmed = line.trim()

    if (!trimmed) {
      flushBullets()
      return
    }

    if (trimmed.startsWith("- ")) {
      bullets.push(trimmed.slice(2))
      return
    }

    flushBullets()
    blocks.push(
      <p
        key={`p-${index}`}
        className={`my-2 ${isBoldHeading(trimmed) ? "font-semibold text-slate-950" : ""}`}
      >
        {renderInline(trimmed)}
      </p>
    )
  })

  flushBullets()

  return <div className="text-sm leading-7">{blocks}</div>
}
