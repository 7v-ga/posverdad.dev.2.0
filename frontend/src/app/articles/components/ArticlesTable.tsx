'use client'

import * as React from 'react'
import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  RowSelectionState,
  SortingState,
  VisibilityState,
  useReactTable,
} from '@tanstack/react-table'

import { useArticlesStore } from '@/store/articles-store'
import type { ArticlesState, ArticlesActions } from '@/store/articles-store'
import type { Article } from '@/lib/schemas'

import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'

import { formatDate } from '@/lib/utils'
import { toCSV, downloadCSV } from '@/lib/csv'
import ArticleDetailDialog from './ArticleDetailDialog'
import EntitiesDialog from './EntitiesDialog'

type Store = ArticlesState & ArticlesActions

const selectItems = (s: Store) => s.items
const selectFilters = (s: Store) => s.filters
const selectSelect = (s: Store) => s.select
const selectSelection = (s: Store) => s.selection
const updateEntity = (s: Store) => s.updateEntity
const addAlias = (s: Store) => s.addAlias

const PAGE_SIZE_KEY = 'postverdad-pageSize-v1'
const COLS_KEY = 'postverdad-cols-v1'

const FEATURE_BULK = process.env['NEXT_PUBLIC_FEATURE_BULK'] === '1'

export default function ArticlesTable() {
  const items = useArticlesStore(selectItems)
  const filters = useArticlesStore(selectFilters)
  const select = useArticlesStore(selectSelect)
  const selection = useArticlesStore(selectSelection)
  const mutateEntity = useArticlesStore(updateEntity)
  const addAliasToEntity = useArticlesStore(addAlias)

  const [sorting, setSorting] = React.useState<SortingState>([])
  const [entitiesOpen, setEntitiesOpen] = React.useState(false)

  const [pageSize, setPageSize] = React.useState<number>(() => {
    if (typeof window === 'undefined') return 20
    const s = localStorage.getItem(PAGE_SIZE_KEY)
    return s ? Number(s) : 20
  })

  const [columnVisibility, setColumnVisibility] = React.useState<VisibilityState>(() => {
    if (typeof window === 'undefined') return {}
    try {
      return JSON.parse(localStorage.getItem(COLS_KEY) || '{}') as VisibilityState
    } catch {
      return {}
    }
  })

  // Selección de filas (solo cuando la flag está activa)
  const [rowSelection, setRowSelection] = React.useState<RowSelectionState>({})

  React.useEffect(() => {
    localStorage.setItem(PAGE_SIZE_KEY, String(pageSize))
  }, [pageSize])

  React.useEffect(() => {
    localStorage.setItem(COLS_KEY, JSON.stringify(columnVisibility))
  }, [columnVisibility])

  // Filtro en cliente
  const filtered = React.useMemo(() => {
    const q = filters.q.toLowerCase()
    return items.filter((a) => {
      if (q && !(`${a.title} ${a.url}`.toLowerCase().includes(q))) return false
      if (filters.sources.length && !filters.sources.includes(a.source)) return false
      if (filters.lenMin != null && a.len_chars < filters.lenMin) return false
      if (filters.lenMax != null && a.len_chars > filters.lenMax) return false
      if (filters.polMin != null && a.polarity < filters.polMin) return false
      if (filters.polMax != null && a.polarity > filters.polMax) return false
      if (filters.subMin != null && a.subjectivity < filters.subMin) return false
      if (filters.subMax != null && a.subjectivity > filters.subMax) return false
      if (filters.dateFrom && new Date(a.published_at) < new Date(filters.dateFrom)) return false
      if (filters.dateTo && new Date(a.published_at) > new Date(filters.dateTo)) return false
      return true
    })
  }, [items, filters])

  // Definición de columnas
  const columns = React.useMemo<ColumnDef<Article>[]>(() => {
    const base: ColumnDef<Article>[] = [
      {
        accessorKey: 'title',
        header: 'Título',
        cell: (ctx) => (
          <a
            className="underline underline-offset-2"
            href={ctx.row.original.url}
            target="_blank"
            rel="noreferrer"
          >
            {ctx.getValue() as string}
          </a>
        ),
      },
      { accessorKey: 'source', header: 'Fuente' },
      {
        accessorKey: 'published_at',
        header: 'Fecha',
        cell: (ctx) => formatDate(ctx.getValue() as string),
      },
      { accessorKey: 'len_chars', header: 'Longitud' },
      { accessorKey: 'polarity', header: 'Polaridad' },
      { accessorKey: 'subjectivity', header: 'Subjetividad' },
      {
        id: 'actions',
        header: 'Acciones',
        cell: ({ row }) => (
          <div className="flex gap-2">
            <Button size="sm" variant="secondary" onClick={() => select(row.original)}>
              Ver detalle
            </Button>
            <Button
              size="sm"
              onClick={() => {
                select(row.original)
                setEntitiesOpen(true)
              }}
            >
              Editar entidades
            </Button>
          </div>
        ),
      },
    ]

    if (!FEATURE_BULK) return base
      
    return [
      {
        id: 'select',
        header: ({ table }) => (
          <Checkbox
            checked={
              table.getIsAllPageRowsSelected() ||
              (table.getIsSomePageRowsSelected() && 'indeterminate')
            }
            onCheckedChange={(v) => table.toggleAllPageRowsSelected(!!v)}
            aria-label="Seleccionar todos (página)"
          />
        ),
        cell: ({ row }) => (
          <Checkbox
            checked={row.getIsSelected()}
            onCheckedChange={(v) => row.toggleSelected(!!v)}
            aria-label="Seleccionar fila"
          />
        ),
        enableSorting: false,
        enableHiding: false,
        size: 32,
      },
      ...base, // ✅ nada más acá
    ]
    
  }, [select])

  // Instancia de TanStack Table
  const table = useReactTable({
    data: filtered,
    columns,
    state: {
      sorting,
      columnVisibility,
      ...(FEATURE_BULK ? { rowSelection } : {}),
    },
    onSortingChange: setSorting,
    onColumnVisibilityChange: setColumnVisibility,
    ...(FEATURE_BULK ? { onRowSelectionChange: setRowSelection, enableRowSelection: true } : {}),
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: { pagination: { pageIndex: 0, pageSize } },
  })

  React.useEffect(() => {
    table.setPageSize(pageSize)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pageSize])

  const hasRows = table.getRowModel().rows.length > 0

  // Helpers Bulk (mock)
  const selectedRows = FEATURE_BULK
    ? table.getRowModel().rows.filter((r) => r.getIsSelected())
    : []
  const selectedCount = selectedRows.length

  const bulkBlock = (blocked: boolean) => {
    if (!FEATURE_BULK || selectedCount === 0) return
    for (const r of selectedRows) {
      const a = r.original
      for (const e of a.entities) {
        mutateEntity(a.id, e.id, { blocked })
      }
    }
    // Simple feedback (si tienes shadcn toast, cámbialo por toast())
    alert(`${blocked ? 'Bloqueadas' : 'Desbloqueadas'} entidades de ${selectedCount} artículo(s).`)
  }

  const bulkAddAlias = () => {
    if (!FEATURE_BULK || selectedCount === 0) return
    const alias = window.prompt('Alias a agregar (se aplicará a TODAS las entidades de la selección):')
    if (!alias) return
    const v = alias.trim()
    if (!v) return
    for (const r of selectedRows) {
      const a = r.original
      for (const e of a.entities) {
        addAliasToEntity(a.id, e.id, v)
      }
    }
    alert(`Alias “${v}” agregado a entidades de ${selectedCount} artículo(s).`)
  }

  return (
    <Card className="p-2">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-2 p-2">
        {/* Beta (flag) */}
        {FEATURE_BULK && (
          <Badge variant="secondary" className="bg-amber-100 text-amber-900">
            Beta
          </Badge>
        )}

        {/* pageSize */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">Filas por página</span>
          <Select value={String(pageSize)} onValueChange={(v) => setPageSize(Number(v))}>
            <SelectTrigger className="h-8 w-24">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="10">10</SelectItem>
              <SelectItem value="20">20</SelectItem>
              <SelectItem value="50">50</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* CSV */}
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            const csv = toCSV(filtered)
            downloadCSV('postverdad_articles.csv', csv)
          }}
        >
          Exportar CSV
        </Button>

        {/* Column toggles */}
        <div className="ml-auto flex flex-wrap items-center gap-2 text-xs">
          {table
            .getAllLeafColumns()
            .filter((c) => c.id !== 'actions' && c.id !== 'select') // no toggle para acciones/checkbox
            .map((col) => (
              <label key={col.id} className="inline-flex items-center gap-1">
                <input
                  type="checkbox"
                  className="accent-foreground"
                  checked={col.getIsVisible()}
                  onChange={(e) => col.toggleVisibility(e.target.checked)}
                />
                <span className="capitalize">{col.id.replace('_', ' ')}</span>
              </label>
            ))}
        </div>
      </div>

      {/* Bulk actions bar (solo con flag y con selección) */}
      {FEATURE_BULK && (
        <div className="flex items-center justify-between gap-2 px-2 pb-2">
          <div className="text-xs text-muted-foreground">
            Seleccionados: <Badge variant="secondary">{selectedCount}</Badge>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" disabled={selectedCount === 0} onClick={() => bulkBlock(true)}>
              Bloquear entidades
            </Button>
            <Button variant="outline" size="sm" disabled={selectedCount === 0} onClick={() => bulkBlock(false)}>
              Desbloquear entidades
            </Button>
            <Button size="sm" disabled={selectedCount === 0} onClick={bulkAddAlias}>
              Agregar alias…
            </Button>
          </div>
        </div>
      )}

      {/* Tabla */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            {table.getHeaderGroups().map((hg) => (
              <tr key={hg.id}>
                {hg.headers.map((h) => {
                  const canSort = h.column.getCanSort()
                  const headerContent = h.isPlaceholder
                    ? null
                    : flexRender(h.column.columnDef.header, h.getContext())
                
                  // ✅ evitar objeto inline en JSX
                  const sortState = h.column.getIsSorted() as false | 'asc' | 'desc'
                  const indicator = sortState === 'asc' ? '▲' : sortState === 'desc' ? '▼' : ''
                
                  return (
                    <th key={h.id} className="text-left px-3 py-2">
                      {h.isPlaceholder ? null : canSort ? (
                        <button
                          onClick={h.column.getToggleSortingHandler()}
                          className="inline-flex items-center gap-1"
                        >
                          {headerContent}
                          {indicator}
                        </button>
                      ) : (
                        <div className="inline-flex items-center gap-1">
                          {headerContent}
                        </div>
                      )}
                    </th>
                  )
                })}
              </tr>
            ))}
          </thead>
          <tbody>
            {hasRows ? (
              table.getRowModel().rows.map((row) => (
                <tr key={row.id} className="border-t">
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-3 py-2">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))
            ) : (
              <tr>
                <td
                  colSpan={table.getAllLeafColumns().length}
                  className="px-3 py-10 text-center text-sm text-muted-foreground"
                >
                  No hay resultados con estos filtros.
                  <Button
                    variant="link"
                    className="ml-1"
                    onClick={() => window.dispatchEvent(new CustomEvent('pv:clearFilters'))}
                  >
                    Limpiar filtros
                  </Button>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between p-2">
        <div className="text-xs text-muted-foreground">
          Mostrando {table.getRowModel().rows.length} de {filtered.length}
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          >
            Anterior
          </Button>
          <Badge variant="secondary">Página {table.getState().pagination.pageIndex + 1}</Badge>
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
          >
            Siguiente
          </Button>
        </div>
      </div>

      {/* Diálogos */}
      <ArticleDetailDialog article={selection} onClose={() => select(null)} />
      <EntitiesDialog open={entitiesOpen} onOpenChange={setEntitiesOpen} />
    </Card>
  )
}
