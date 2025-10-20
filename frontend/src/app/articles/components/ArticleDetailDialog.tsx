'use client'

import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { formatDate } from '@/lib/utils'
import type { Article } from '@/lib/schemas'

export default function ArticleDetailDialog({
  article,
  onClose,
}: {
  article: Article | null
  onClose: () => void
}) {
  return (
    <Dialog open={!!article} onOpenChange={(o) => { if (!o) onClose() }}>
      <DialogContent className="max-w-2xl">
        {article && (
          <>
            <DialogHeader>
              <DialogTitle className="text-lg">{article.title}</DialogTitle>
            </DialogHeader>
            <div className="space-y-3 text-sm">
              <div><span className="font-medium">Fuente:</span> {article.source}</div>
              <div><span className="font-medium">Fecha:</span> {formatDate(article.published_at)}</div>
              <div className="flex gap-2">
                <Badge variant="secondary">Len: {article.len_chars}</Badge>
                <Badge variant="secondary">Pol: {article.polarity}</Badge>
                <Badge variant="secondary">Subj: {article.subjectivity}</Badge>
              </div>
              <div>
                <a className="underline" href={article.url} target="_blank" rel="noreferrer">
                  Abrir URL
                </a>
              </div>
              <div>
                <div className="font-medium mb-1">Entidades</div>
                <div className="flex flex-wrap gap-2">
                  {article.entities.map((e) => (
                    <Badge key={e.id}>{e.type}: {e.name}</Badge>
                  ))}
                </div>
              </div>
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
