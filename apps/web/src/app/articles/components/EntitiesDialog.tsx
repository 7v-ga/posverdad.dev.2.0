'use client'

import { useState } from 'react'
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

  const normalizedEntities = sel?.entities ?? []

  // Entidades crudas desde preprocessed_data.entities (si el backend las expone)
  const rawJsonEntities = (sel as any)?.preprocessed_data?.entities ?? []

  const hasNormalized = normalizedEntities.length > 0
  const hasRaw = rawJsonEntities.length > 0

  const [local, setLocal] = useState(normalizedEntities)

  // Estos métodos pueden llamarse distinto en tu store.
  // Usamos `as any` para no pelear con TypeScript si la forma exacta difiere.
  const updateEntity = useArticlesStore((s) => (s as any).updateEntity)
  const addAlias = useArticlesStore((s) => (s as any).addAlias)
  const removeAlias = useArticlesStore((s) => (s as any).removeAlias)

  // aliasInputs por entidad (key = entity.id)
  const [aliasInputs, setAliasInputs] = useState<Record<string, string>>({})

  // Si no hay artículo seleccionado, no mostramos nada
  if (!sel) return null

  // Entities defensivo: si por alguna razón no viene `entities`, usamos []
  const entities: any[] = ((sel as any).entities ?? []) as any[]

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
          {entities.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              Este artículo no tiene entidades asociadas.
            </p>
          ) : (
            entities.map((e) => {
              const aliasValue = aliasInputs[String(e.id)] ?? ''
              const aliases: string[] = (e.aliases ?? []) as string[]

              return (
                <div key={e.id} className="border rounded-md p-3">
                  <div className="flex items-center gap-2">
                    <div className="font-medium text-xs uppercase tracking-wide">{e.type}</div>
                    <div className="flex-1">{e.name}</div>
                    <label className="flex items-center gap-2 text-sm">
                      <Checkbox
                        checked={!!e.blocked}
                        onCheckedChange={(v) => {
                          if (!updateEntity) return
                          updateEntity((sel as any).id, e.id, { blocked: !!v })
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
                            {removeAlias && (
                              <button
                                type="button"
                                className="ml-2 text-muted-foreground hover:text-foreground"
                                onClick={() => removeAlias((sel as any).id, e.id, a)}
                              >
                                ×
                              </button>
                            )}
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
                          if (!trimmed || !addAlias) return
                          addAlias((sel as any).id, e.id, trimmed)
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
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
