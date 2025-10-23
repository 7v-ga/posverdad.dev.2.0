import { Badge } from "@/components/ui/badge"

type Role = "admin" | "read"

export function RoleBadge({ role }: { role: Role }) {
  const text = role === "admin" ? "admin" : "lectura"
  const className =
    role === "admin"
      ? "bg-red-100 text-red-900 dark:bg-red-900/30 dark:text-red-200"
      : "bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-slate-200"

  return <Badge className={className}>{text}</Badge>
}
