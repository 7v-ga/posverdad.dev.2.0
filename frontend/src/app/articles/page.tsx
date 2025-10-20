'use client'


export default function ArticlesPage() {
const { items, setItems, setLoading, loading, filters, setFilters } = useArticlesStore()
const [error, setError] = useState<string | null>(null)


const pathname = usePathname()
const searchParams = useSearchParams()
const router = useRouter()


// Hidratar filtros desde URL al cargar
useEffect(() => {
const qs = fromQS(searchParams as unknown as URLSearchParams)
const next = {
q: qs.str('q'),
sources: qs.arr('source'),
dateFrom: qs.iso('from'),
dateTo: qs.iso('to'),
lenMin: qs.num('lenMin'),
lenMax: qs.num('lenMax'),
polMin: qs.num('polMin'),
polMax: qs.num('polMax'),
subMin: qs.num('subMin'),
subMax: qs.num('subMax'),
}
setFilters(next)
// eslint-disable-next-line react-hooks/exhaustive-deps
}, [])


// Empujar cambios de filtros a la URL (replaceState)
useEffect(() => {
const qs = toQS({
q: filters.q,
source: filters.sources,
from: filters.dateFrom ?? undefined,
to: filters.dateTo ?? undefined,
lenMin: filters.lenMin ?? undefined,
lenMax: filters.lenMax ?? undefined,
polMin: filters.polMin ?? undefined,
polMax: filters.polMax ?? undefined,
subMin: filters.subMin ?? undefined,
subMax: filters.subMax ?? undefined,
})
router.replace(`${pathname}${qs}`, { scroll: false })
}, [filters, pathname, router])


// Data mock
useEffect(() => {
let mounted = true
async function load() {
setLoading(true)
try {
const res = await fetch('/api/articles')
const data = (await res.json()) as ArticlesResponse
if (!mounted) return
setItems(data.items, data.total)
} catch (e) {
setError('No se pudieron cargar los artículos')
} finally {
setLoading(false)
}
}
if (items.length === 0) load()
return () => { mounted = false }
}, [items.length, setItems, setLoading])


const content = useMemo(() => {
if (loading) return <Skeleton className="h-64 w-full" />
if (error) return <div className="text-red-600">{error}</div>
return (
<div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
<aside className="lg:col-span-1"><ArticlesFilters /></aside>
<section className="lg:col-span-3"><ArticlesTable /></section>
</div>
)
}, [loading, error])


return content
}