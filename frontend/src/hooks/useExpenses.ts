import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AxiosError } from 'axios'
import { expensesApi, type Expense, type PaginatedResponse } from '@/lib/api'
import { useUIStore } from '@/lib/store'

interface ExpenseFilters {
  category_id?: number | null
  start_date?: string | null
  end_date?: string | null
  page?: number
  per_page?: number
}

export function useExpenses(filters: ExpenseFilters = {}) {
  const queryClient = useQueryClient()
  const { setFormError, clearFormError } = useUIStore()

  const queryParams = {
    ...(filters.category_id !== undefined && filters.category_id !== null
      ? { category_id: filters.category_id }
      : {}),
    ...(filters.start_date ? { start_date: filters.start_date } : {}),
    ...(filters.end_date ? { end_date: filters.end_date } : {}),
    page: filters.page ?? 1,
    per_page: filters.per_page ?? 50,
  }

  const expensesQuery = useQuery({
    queryKey: ['expenses', queryParams],
    queryFn: () => expensesApi.getAll(queryParams),
  })

  const paginatedData = expensesQuery.data as PaginatedResponse<Expense> | undefined
  const expenses = paginatedData?.items ?? []
  const meta = paginatedData?.meta

  const createExpense = useMutation({
    mutationFn: expensesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expenses'] })
      queryClient.invalidateQueries({ queryKey: ['summary'] })
      clearFormError()
    },
    onError: (error: AxiosError<{ detail?: string }>) => {
      const message = error.response?.data?.detail || 'Erreur lors de la création de la dépense'
      setFormError(message)
    },
  })

  const updateExpense = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Partial<Expense> }) =>
      expensesApi.update(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expenses'] })
      queryClient.invalidateQueries({ queryKey: ['summary'] })
      clearFormError()
    },
    onError: (error: AxiosError<{ detail?: string }>) => {
      const message = error.response?.data?.detail || 'Erreur lors de la mise à jour de la dépense'
      setFormError(message)
    },
  })

  const deleteExpense = useMutation({
    mutationFn: expensesApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expenses'] })
      queryClient.invalidateQueries({ queryKey: ['summary'] })
      clearFormError()
    },
    onError: (error: AxiosError<{ detail?: string }>) => {
      const message = error.response?.data?.detail || 'Erreur lors de la suppression de la dépense'
      setFormError(message)
    },
  })

  return {
    expensesQuery,
    expenses,
    meta,
    createExpense,
    updateExpense,
    deleteExpense,
    isCreating: createExpense.isPending,
    isUpdating: updateExpense.isPending,
    isDeleting: deleteExpense.isPending,
  }
}
