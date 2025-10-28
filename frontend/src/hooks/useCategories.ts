import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AxiosError } from 'axios'
import { categoriesApi, type Category } from '@/lib/api'
import { useUIStore } from '@/lib/store'

export function useCategories() {
  const queryClient = useQueryClient()
  const { setFormError, clearFormError } = useUIStore()

  // Query pour récupérer toutes les catégories
  const categoriesQuery = useQuery({
    queryKey: ['categories', { page: 1, per_page: 100 }],
    queryFn: () => categoriesApi.getAll({ page: 1, per_page: 100 }),
    select: (data) => data.items,
  })

  // Mutation pour créer une catégorie
  const createCategory = useMutation({
    mutationFn: categoriesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] })
      clearFormError()
    },
    onError: (error: AxiosError<{ detail?: string }>) => {
      const message = error.response?.data?.detail || 'Erreur lors de la création de la catégorie'
      setFormError(message)
    },
  })

  // Mutation pour mettre à jour une catégorie
  const updateCategory = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Partial<Category> }) =>
      categoriesApi.update(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] })
      clearFormError()
    },
    onError: (error: AxiosError<{ detail?: string }>) => {
      const message = error.response?.data?.detail || 'Erreur lors de la mise à jour de la catégorie'
      setFormError(message)
    },
  })

  // Mutation pour supprimer une catégorie
  const deleteCategory = useMutation({
    mutationFn: categoriesApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] })
      clearFormError()
    },
    onError: (error: AxiosError<{ detail?: string }>) => {
      const message = error.response?.data?.detail || 'Erreur lors de la suppression de la catégorie'
      setFormError(message)
    },
  })

  return {
    categoriesQuery,
    createCategory,
    updateCategory,
    deleteCategory,
    isCreating: createCategory.isPending,
    isUpdating: updateCategory.isPending,
    isDeleting: deleteCategory.isPending,
  }
}
