'use client'

import { useEffect, useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Checkbox } from '@/components/ui/checkbox'
import { useArticlesStore } from '@/store/articles-store'

type EntitiesDialogProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export default function EntitiesDialog({ open, onOpenChange }: EntitiesDialogProps) {
  const sel = useArticlesStore((s) => s.selection)

  const updateEntity = useArticlesStore((s) => s.updateEntity)
  const addAlias = useArticlesStore((s) => s.addAlias)
  const removeAlias = useArticlesStore((s) => s.removeAlias)

  const normalizedEntities = sel?.entities ?? []

  const rawJsonEntities: any[] =
    sel &&
    (sel as any).preprocessed_data &&
    typeof (sel as any).preprocessed_data === 'object' &&
    Array.isArray((sel as any).preprocessed_data.entities)
      ? (sel as any).preprocessed_data.entities
      : []

  const hasNormalized = normalizedEntities.length > 0
  const hasRaw = rawJsonEntities.length > 0

  // aliasInputs por entidad (key = entity.id)
  const [aliasInputs, setAliasInputs] = useState<Record<string, string>>({})

  // Resetear inputs cuando cambia de artículo
  useEffect(() => {
    setAliasInputs({})
  }, [sel?.id])

  // Si no hay artículo seleccionado, no mostramos nada
  if (!sel) return null

  const handleOpenChange = (nextOpen: boolean) => {
    onOpenChange(nextOpen)
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>Editar entidades — {(sel as any).title}</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* Entidades normalizadas (editables) */}
          {hasNormalized ? (
            normalizedEntities.map((e) => {
              const aliasValue = aliasInputs[String(e.id)] ?? ''
              const aliases: string[] = e.aliases ?? []

              return (
                <div key={e.id} className="border rounded-md p-3">
                  <div className="flex items-center gap-2">
                    <div className="font-medium text-xs uppercase tracking-wide">{e.type}</div>
                    <div className="flex-1">{e.name}</div>
                    <label className="flex items-center gap-2 text-sm">
                      <Checkbox
                        checked={!!e.blocked}
                        onCheckedChange={(v) => {
                          updateEntity(sel.id, e.id, { blocked: !!v })
                        }}
                      />
                      Bloqueada
                    </label>
                  </div>

                  <div className="mt-3">
                    <div className="text-xs text-muted-foreground mb-1">Aliases</div>
                    <div className="flex flex-wrap gap-2 mb-2">
                      {aliases.length > 0 ? (
                        aliases.map((a) => (
                          <span key={a} className="px-2 py-1 text-xs bg-muted rounded">
                            {a}
                            <button
                              type="button"
                              className="ml-2 text-muted-foreground hover:text-foreground"
                              onClick={() => removeAlias(sel.id, e.id, a)}
                            >
                              ×
                            </button>
                          </span>
                        ))
                      ) : (
                        <span className="text-xs text-muted-foreground">
                          Sin aliases registrados.
                        </span>
                      )}
                    </div>

                    <div className="flex gap-2">
                      <Input
                        placeholder="Nuevo alias"
                        value={aliasValue}
                        onChange={(ev) =>
                          setAliasInputs((prev) => ({
                            ...prev,
                            [String(e.id)]: ev.target.value,
                          }))
                        }
                      />
                      <Button
                        type="button"
                        onClick={() => {
                          const trimmed = aliasValue.trim()
                          if (!trimmed) return
                          addAlias(sel.id, e.id, trimmed)
                          setAliasInputs((prev) => ({
                            ...prev,
                            [String(e.id)]: '',
                          }))
                        }}
                      >
                        Agregar
                      </Button>
                    </div>
                  </div>
                </div>
              )
            })
          ) : (
            <p className="text-sm text-muted-foreground">
              Este artículo no tiene entidades normalizadas asociadas.
            </p>
          )}

          {/* Entidades crudas desde preprocessed_data.entities (solo lectura) */}
          {hasRaw && !hasNormalized && (
            <div className="space-y-2">
              <div className="text-sm font-medium">Entidades crudas (solo lectura)</div>
              <div className="text-xs text-muted-foreground">
                Estas entidades provienen de <code>preprocessed_data.entities</code> y aún no están
                vinculadas al sistema de edición.
              </div>
              <div className="flex flex-wrap gap-2 mt-1">
                {rawJsonEntities.map((e, idx) => (
                  <span
                    key={`${e.label ?? 'ENT'}-${idx}`}
                    className="inline-flex items-center rounded-full border px-2 py-0.5 text-xs"
                  >
                    <span className="mr-1 font-semibold">{e.label ?? 'ENT'}</span>
                    <span>{e.text ?? e.name}</span>
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
