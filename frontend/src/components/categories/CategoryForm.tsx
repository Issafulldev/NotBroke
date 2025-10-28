'use client'

import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useTranslations } from '@/hooks/useTranslations'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useCategories } from '@/hooks/useCategories'
import { type Category } from '@/lib/api'

interface CategoryFormValues {
  name: string
  description: string
  parent_id: string
}

export interface CategorySubmitData {
  name: string
  description: string
  parent_id: number | null
}

interface CategoryFormProps {
  category?: Category | null
  onSubmit: (data: CategorySubmitData) => void
  onCancel?: () => void
  isSubmitting?: boolean
}

export function CategoryForm({ category, onSubmit, onCancel, isSubmitting }: CategoryFormProps) {
  const { categoriesQuery } = useCategories()
  const { t } = useTranslations()

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors },
  } = useForm<CategoryFormValues>({
    defaultValues: {
      name: '',
      description: '',
      parent_id: '',
    },
  })

  const categories = categoriesQuery.data ?? []

  useEffect(() => {
    if (category) {
      reset({
        name: category.name ?? '',
        description: category.description ?? '',
        parent_id: category.parent_id ? String(category.parent_id) : 'none',
      })
    } else {
      reset({
        name: '',
        description: '',
        parent_id: 'none',
      })
    }
  }, [category, reset])

  // Fonction pour construire la hiérarchie des catégories
  const buildCategoryOptions = (categories: Category[], excludeId?: number) => {
    const options: Array<{ value: string; label: string; disabled?: boolean }> = [
      { value: 'none', label: t('categories.parent') },
    ]

    const addCategoryToOptions = (cats: Category[], depth = 0) => {
      cats.forEach((cat) => {
        if (cat.id !== excludeId) {
          options.push({
            value: String(cat.id),
            label: `${'— '.repeat(depth)}${cat.name}`,
          })
        }
        if (cat.children && cat.children.length > 0) {
          addCategoryToOptions(cat.children, depth + 1)
        }
      })
    }

    addCategoryToOptions(categories)
    return options
  }

  const categoryOptions = buildCategoryOptions(categories, category?.id)

  const handleFormSubmit = (data: CategoryFormValues) => {
    const payload = {
      ...data,
      parent_id: data.parent_id && data.parent_id !== 'none' ? Number(data.parent_id) : null,
    }
    onSubmit(payload)
  }

  return (
    <Card className="shadow-lg">
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-2 text-xl">
          <div className="p-2 bg-primary/10 rounded-lg">
            📁
          </div>
          {category ? t('categories.editButton') : t('categories.addButton')}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
          <div className="space-y-3">
            <Label htmlFor="name" className="text-sm font-medium">
              {t('categories.name')}
            </Label>
            <Input
              id="name"
              placeholder={t('categories.name')}
              className="h-11"
              {...register('name', {
                required: t('categories.name') + ' ' + 'obligatoire',
                maxLength: { value: 100, message: 'Maximum 100 caractères' }
              })}
            />
            {errors.name && (
              <p className="text-sm text-destructive flex items-center gap-1">
                <span className="text-destructive">⚠️</span>
                {errors.name.message}
              </p>
            )}
          </div>

          <div className="space-y-3">
            <Label htmlFor="description" className="text-sm font-medium">
              {t('categories.description')}
            </Label>
            <Textarea
              id="description"
              rows={3}
              placeholder={t('categories.description')}
              className="resize-none"
              {...register('description', {
                maxLength: { value: 500, message: 'Erreur' }
              })}
            />
            {errors.description && (
              <p className="text-sm text-destructive flex items-center gap-1">
                <span className="text-destructive">⚠️</span>
                {errors.description.message}
              </p>
            )}
          </div>

          <div className="space-y-3">
            <Label htmlFor="parent_id" className="text-sm font-medium">
              {t('categories.parent')}
            </Label>
            <Select
              value={watch('parent_id')}
              onValueChange={(value) => setValue('parent_id', value)}
            >
              <SelectTrigger className="h-11">
                <SelectValue placeholder={t('categories.parent')} />
              </SelectTrigger>
              <SelectContent>
                {categoryOptions.map((option) => (
                  <SelectItem
                    key={option.value}
                    value={option.value}
                    disabled={option.disabled}
                  >
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex gap-3 pt-4 border-t">
            <Button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 h-11 min-w-0 text-xs"
            >
              {isSubmitting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  {t('categories.save')}...
                </>
              ) : (
                category ? t('categories.save') : t('categories.addButton')
              )}
            </Button>
            {onCancel && (
              <Button
                type="button"
                variant="outline"
                onClick={onCancel}
                className="h-11 px-6 flex-shrink-0"
              >
                {t('categories.cancel')}
              </Button>
            )}
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
