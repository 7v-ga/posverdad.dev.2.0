'use client'

import { useEffect, useMemo, useState } from 'react'
// ✅ evitamos importar desde @radix-ui/react-checkbox
type CheckedState = boolean | 'indeterminate'

import { Card } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Checkbox } from '@/components/ui/checkbox'
import { Slider } from '@/components/ui/slider'
import { Separator } from '@/components/ui/separator'
import { useArticlesStore } from '@/store/articles-store'

export default function ArticlesFilters() {
  const { items, filters, setFilters, clearFilters } = useArticlesStore()
  const [len, setLen] = useState<[number, number]>([filters.lenMin ?? 0, filters.lenMax ?? 8000])
  const [pol, setPol] = useState<[number, number]>([filters.polMin ?? -1, filters.polMax ?? 1])
  const [sub, setSub] = useState<[number, number]>([filters.subMin ?? 0, filters.subMax ?? 1])

  // Permite limpiar desde el botón global de la tabla (evento custom)
  useEffect(() => {
    const h = () => {
      clearFilters()
      // Sincroniza sliders con el estado reseteado
      setLen([0, 8000])
      setPol([-1, 1])
      setSub([0, 1])
    }
    window.addEventListener('pv:clearFilters', h as EventListener)
    return () => window.removeEventListener('pv:clearFilters', h as EventListener)
  }, [clearFilters])

  // Si los filtros cambian externamente (e.g., URL), sincroniza sliders
  useEffect(() => {
    setLen([filters.lenMin ?? 0, filters.lenMax ?? 8000])
    setPol([filters.polMin ?? -1, filters.polMax ?? 1])
    setSub([filters.subMin ?? 0, filters.subMax ?? 1])
  }, [
    filters.lenMin,
    filters.lenMax,
    filters.polMin,
    filters.polMax,
    filters.subMin,
    filters.subMax,
  ])

  const sources = useMemo(() => Array.from(new Set(items.map((i) => i.source))).sort(), [items])

  return (
    <Card className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <div className="font-medium">Filtros</div>
        <button
          className="text-sm underline"
          onClick={() => {
            clearFilters()
            setLen([0, 8000])
            setPol([-1, 1])
            setSub([0, 1])
          }}
        >
          Limpiar
        </button>
      </div>

      <div className="space-y-2">
        <Label>Fuente</Label>
        <div className="grid grid-cols-1 gap-1">
          {sources.map((s) => (
            <label key={s} className="flex items-center gap-2 text-sm">
              <Checkbox
                checked={filters.sources.includes(s)}
                onCheckedChange={(v: CheckedState) => {
                  const set = new Set(filters.sources)
                  if (v === true) set.add(s)
                  else set.delete(s)
                  setFilters({ sources: Array.from(set) })
                }}
              />
              <span>{s}</span>
            </label>
          ))}
        </div>
      </div>

      <Separator />

      <div className="space-y-2">
        <Label>Longitud (caracteres)</Label>
        <Slider
          min={0}
          max={8000}
          step={100}
          value={len}
          onValueChange={(v: number[]) => setLen(v as [number, number])}
          onValueCommit={(v: number[]) => {
            const [min, max] = v as [number, number]
            setFilters({ lenMin: min, lenMax: max })
          }}
        />
        <div className="text-xs text-muted-foreground">
          {len[0]} – {len[1]}
        </div>
      </div>

      <div className="space-y-2">
        <Label>Polaridad</Label>
        <Slider
          min={-1}
          max={1}
          step={0.05}
          value={pol}
          onValueChange={(v: number[]) => setPol(v as [number, number])}
          onValueCommit={(v: number[]) => {
            const [min, max] = v as [number, number]
            setFilters({ polMin: min, polMax: max })
          }}
        />
        <div className="text-xs text-muted-foreground">
          {pol[0].toFixed(2)} – {pol[1].toFixed(2)}
        </div>
      </div>

      <div className="space-y-2">
        <Label>Subjetividad</Label>
        <Slider
          min={0}
          max={1}
          step={0.05}
          value={sub}
          onValueChange={(v: number[]) => setSub(v as [number, number])}
          onValueCommit={(v: number[]) => {
            const [min, max] = v as [number, number]
            setFilters({ subMin: min, subMax: max })
          }}
        />
        <div className="text-xs text-muted-foreground">
          {sub[0].toFixed(2)} – {sub[1].toFixed(2)}
        </div>
      </div>

      <Separator />

      <div className="space-y-2">
        <Label>Fecha (YYYY-MM-DD)</Label>
        <div className="grid grid-cols-2 gap-2">
          <Input
            placeholder="Desde"
            type="date"
            onChange={(e) =>
              setFilters({
                dateFrom: e.target.value ? new Date(e.target.value).toISOString() : null,
              })
            }
          />
          <Input
            placeholder="Hasta"
            type="date"
            onChange={(e) =>
              setFilters({
                dateTo: e.target.value ? new Date(e.target.value).toISOString() : null,
              })
            }
          />
        </div>
      </div>
    </Card>
  )
}
