import { Article } from './schemas'


function escapeCSV(val: string) {
if (/[",
]/.test(val)) return '"' + val.replace(/"/g, '""') + '"'
return val
}


export function toCSV(rows: Article[]): string {
const headers = [
'id','title','url','source','published_at','len_chars','polarity','subjectivity'
]
const lines = [headers.join(',')]
for (const r of rows) {
lines.push([
r.id,
escapeCSV(r.title),
r.url,
escapeCSV(r.source),
r.published_at,
String(r.len_chars),
String(r.polarity),
String(r.subjectivity),
].join(','))
}
return lines.join('
')
}


export function downloadCSV(filename: string, csv: string) {
const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
const url = URL.createObjectURL(blob)
const a = document.createElement('a')
a.href = url
a.download = filename
a.click()
URL.revokeObjectURL(url)
}