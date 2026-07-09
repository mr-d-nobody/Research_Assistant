export default function Limit({ label, used, limit }) {
  const isUnlimited = limit == null
  const percent = isUnlimited ? 100 : Math.min(100, Math.round((used / limit) * 100))

  return (
    <div className="mt-4">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium text-slate-700">{label}</span>
        <span className="text-slate-500">
          {isUnlimited ? "Unlimited" : `${used}/${limit}`}
        </span>
      </div>
      <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100">
        <div className="h-full rounded-full bg-emerald-600" style={{ width: `${percent}%` }} />
      </div>
    </div>
  )
}
