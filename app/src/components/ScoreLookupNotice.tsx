interface ScoreLookupNoticeProps {
  title: string;
  description: string;
  tone?: "warning" | "info";
}

export function ScoreLookupNotice({
  title,
  description,
  tone = "warning",
}: ScoreLookupNoticeProps) {
  const styles =
    tone === "warning"
      ? "border-amber-200 bg-amber-50 text-amber-900"
      : "border-sky-200 bg-sky-50 text-sky-900";

  return (
    <div className={`rounded-3xl border px-4 py-4 text-sm leading-6 ${styles}`}>
      <p className="font-semibold">{title}</p>
      <p className="mt-1">{description}</p>
    </div>
  );
}
