export type QS = Record<string, string | number | boolean | string[] | null | undefined>


export function toQS(obj: QS): string {
const sp = new URLSearchParams()
for (const [k, v] of Object.entries(obj)) {
if (v == null) continue
if (Array.isArray(v)) {
if (v.length === 0) continue
for (const it of v) sp.append(k, String(it))
} else {
const s = String(v)
if (s === '') continue
sp.set(k, s)
}
}
const s = sp.toString()
return s ? `?${s}` : ''
}


export function fromQS(sp: URLSearchParams) {
const str = (k: string) => sp.get(k) ?? ''
const arr = (k: string) => sp.getAll(k)
const num = (k: string) => {
const v = sp.get(k)
if (v == null || v === '') return null
const n = Number(v)
return Number.isFinite(n) ? n : null
}
const iso = (k: string) => {
const v = sp.get(k)
if (!v) return null
const d = new Date(v)
return isNaN(+d) ? null : d.toISOString()
}
const bool = (k: string) => (sp.get(k) === '1' || sp.get(k) === 'true') || false
return { str, arr, num, iso, bool }
}