export default function FeatureCard({ icon: Icon, text }) {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-slate-200 bg-white px-4 py-3 shadow-sm">
      <Icon className="h-5 w-5 text-emerald-700" />
      <span className="text-sm font-medium text-slate-700">{text}</span>
    </div>
  )
}
