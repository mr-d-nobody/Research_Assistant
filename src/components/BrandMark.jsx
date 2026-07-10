import logo from "../assets/researchops-ai-logo.png"


export default function BrandMark({ size = "md", stacked = false }) {
  const imageSize = size === "lg" ? "h-12 w-12" : size === "sm" ? "h-9 w-9" : "h-10 w-10"
  const titleSize = size === "lg" ? "text-xl sm:text-2xl" : size === "sm" ? "text-sm" : "text-lg"

  return (
    <div className={`flex min-w-0 items-center gap-3 ${stacked ? "flex-col text-center" : ""}`}>
      <img
        src={logo}
        alt=""
        className={`${imageSize} shrink-0 rounded-xl border border-slate-200 bg-white object-cover shadow-sm`}
      />
      <div className="min-w-0">
        <div className={`truncate font-semibold tracking-normal text-slate-950 ${titleSize}`}>
          ResearchOps AI
        </div>
        {size === "lg" && (
          <div className="mt-1 text-sm font-medium text-slate-500">
            Research workspace
          </div>
        )}
      </div>
    </div>
  )
}
