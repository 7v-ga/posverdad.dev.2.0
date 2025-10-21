import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(iso: string) {
  // Formato corto en español de Chile
  try {
    return new Date(iso).toLocaleString('es-CL', { dateStyle: 'medium' })
  } catch {
    return iso
  }
}
