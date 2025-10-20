'use client'

import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Checkbox } from '@/components/ui/checkbox'
import { useArticlesStore } from '@/store/articles-store'
import { useState } from 'react'

export default function EntitiesDialog({
  open,
  onOpenChange,
}: {
  open: boolean
  onOpenChange: (v: boolean) => void
}) {
  const sel = useArticlesStore((s) => s.selection)
  const update = useArticlesStore((s) => s.updateEntity)
  const addAlias = useArticlesStore((s) => s.addAlias)
  const removeAlias = useArticlesStore((s) => s.removeAlias)
  const [aliasInput, setAliasInput] = useState('')

  if (!sel) return null

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>Editar entidades — {sel.title}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          {sel.entities.map((e) => (
            <div key={e.id} className="border rounded-md p-3">
              <div className="flex items-center gap-2">
                <div className="font-medium">{e.type}</div>
                <div className="flex-1">{e.name}</div>
                <label className="flex items-center gap-2 text-sm">
                  <Checkbox
                    checked={e.blocked}
                    onCheckedChange={(v) => update(sel.id, e.id, { blocked: !!v })}
                  />
                  Bloqueada
                </label>
              </div>

              <div className="mt-2">
                <div className="text-xs text-muted-foreground mb-1">Aliases</div>
                <div className="flex flex-wrap gap-2 mb-2">
                  {e.aliases.map((a) => (
                    <span key={a} className="px-2 py-1 text-xs bg-muted rounded">
                      {a}
                      <button
                        className="ml-2 text-muted-foreground hover:text-foreground"
                        onClick={() => removeAlias(sel.id, e.id, a)}
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
                <div className="flex gap-2">
                  <Input
                    placeholder="Nuevo alias"
                    value={aliasInput}
                    onChange={(ev) => setAliasInput(ev.target.value)}
                  />
                  <Button
                    onClick={() => {
                      const v = aliasInput.trim()
                      if (v) {
                        addAlias(sel.id, e.id, v)
                        setAliasInput('')
                      }
                    }}
                  >
                    Agregar
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  )
}
