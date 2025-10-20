'use client'
{table.getAllLeafColumns().filter(c => c.id !== 'actions').map((col) => (
<label key={col.id} className="inline-flex items-center gap-1">
<input
type="checkbox"
className="accent-foreground"
checked={col.getIsVisible()}
onChange={(e) => col.toggleVisibility(e.target.checked)}
/>
<span className="capitalize">{col.id.replace('_',' ')}</span>
</label>
))}
</div>
</div>


{/* Tabla */}
<div className="overflow-x-auto">
<table className="w-full text-sm">
<thead>
{table.getHeaderGroups().map(hg => (
<tr key={hg.id}>
{hg.headers.map(h => (
<th key={h.id} className="text-left px-3 py-2">
{h.isPlaceholder ? null : (
<button onClick={h.column.getToggleSortingHandler()} className="inline-flex items-center gap-1">
{flexRender(h.column.columnDef.header, h.getContext())}
{{ asc: '▲', desc: '▼' }[h.column.getIsSorted() as string] ?? ''}
</button>
)}
</th>
))}
</tr>
))}
</thead>
<tbody>
{hasRows ? (
table.getRowModel().rows.map(row => (
<tr key={row.id} className="border-t">
{row.getVisibleCells().map(cell => (
<td key={cell.id} className="px-3 py-2">
{flexRender(cell.column.columnDef.cell, cell.getContext())}
</td>
))}
</tr>
))
) : (
<tr>
<td colSpan={table.getAllLeafColumns().length} className="px-3 py-10 text-center text-sm text-muted-foreground">
No hay resultados con estos filtros.
<Button variant="link" className="ml-1" onClick={() => window.dispatchEvent(new CustomEvent('pv:clearFilters'))}>Limpiar filtros</Button>
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
<Button variant="outline" size="sm" onClick={() => table.previousPage()} disabled={!table.getCanPreviousPage()}>
Anterior
</Button>
<Badge variant="secondary">Página {table.getState().pagination.pageIndex + 1}</Badge>
<Button variant="outline" size="sm" onClick={() => table.nextPage()} disabled={!table.getCanNextPage()}>
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