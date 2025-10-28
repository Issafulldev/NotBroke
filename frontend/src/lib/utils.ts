import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDateOnly(input: string | Date | null | undefined): string {
  if (!input) return ''
  const str = typeof input === 'string' ? input : (input as Date).toISOString()
  if (str.includes('T')) return str.split('T')[0]
  const m = str.match(/\d{4}-\d{2}-\d{2}/)
  return m ? m[0] : str
}

// tree helpers removed (API now returns an already-built tree)
