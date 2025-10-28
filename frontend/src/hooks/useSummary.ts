import { useQuery } from '@tanstack/react-query'
import { summaryApi } from '@/lib/api'

export interface SummaryFilters {
  start_date?: string
  end_date?: string
  category_id?: number
}

export function useMonthlySummary(filters: SummaryFilters = {}) {
  return useQuery({
    queryKey: ['summary', filters],
    queryFn: () => summaryApi.get(filters),
    placeholderData: {
      total: 0,
      category_totals: {},
      start_date: '',
      end_date: '',
      category_id: null,
    },
  })
}
