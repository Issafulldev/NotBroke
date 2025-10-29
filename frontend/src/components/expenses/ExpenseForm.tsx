'use client'

import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { Calendar, DollarSign } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { useTranslations } from '@/hooks/useTranslations'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useCategories } from '@/hooks/useCategories'
import { useCategoryStore } from '@/lib/store'
import { getCurrencySymbol, getDefaultCurrencyByLocale } from '@/lib/utils'
import { type Expense, type Category } from '@/lib/api'

interface ExpenseFormValues {
  amount: number
  currency: string
  description: string
  category_id: number
  date: string
}

export interface ExpenseSubmitData {
  amount: number
  currency: string
  note: string
  category_id: number
  date: string
}

// Liste des devises supportées avec leurs symboles
const SUPPORTED_CURRENCIES = [
  { code: 'EUR', symbol: '€', name: 'Euro' },
  { code: 'USD', symbol: '$', name: 'US Dollar' },
  { code: 'GBP', symbol: '£', name: 'British Pound' },
  { code: 'JPY', symbol: '¥', name: 'Japanese Yen' },
  { code: 'CHF', symbol: 'CHF', name: 'Swiss Franc' },
  { code: 'CAD', symbol: 'C$', name: 'Canadian Dollar' },
  { code: 'AUD', symbol: 'A$', name: 'Australian Dollar' },
  { code: 'NZD', symbol: 'NZ$', name: 'New Zealand Dollar' },
  { code: 'SEK', symbol: 'kr', name: 'Swedish Krona' },
  { code: 'NOK', symbol: 'kr', name: 'Norwegian Krone' },
  { code: 'DKK', symbol: 'kr', name: 'Danish Krone' },
  { code: 'PLN', symbol: 'zł', name: 'Polish Zloty' },
  { code: 'CZK', symbol: 'Kč', name: 'Czech Koruna' },
  { code: 'HUF', symbol: 'Ft', name: 'Hungarian Forint' },
  { code: 'RUB', symbol: '₽', name: 'Russian Ruble' },
  { code: 'TRY', symbol: '₺', name: 'Turkish Lira' },
  { code: 'CNY', symbol: '¥', name: 'Chinese Yuan' },
  { code: 'INR', symbol: '₹', name: 'Indian Rupee' },
  { code: 'BRL', symbol: 'R$', name: 'Brazilian Real' },
  { code: 'ZAR', symbol: 'R', name: 'South African Rand' },
  { code: 'MXN', symbol: '$', name: 'Mexican Peso' },
  { code: 'SGD', symbol: 'S$', name: 'Singapore Dollar' },
  { code: 'HKD', symbol: 'HK$', name: 'Hong Kong Dollar' },
  { code: 'KRW', symbol: '₩', name: 'South Korean Won' },
] as const

// Fonction de formatage avec devise
const formatCurrency = (amount: number, currency: string = 'EUR') => {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(amount);
};

// Le symbole de devise est maintenant importé depuis utils.ts

interface ExpenseFormProps {
  expense?: Expense | null
  onSubmit: (data: ExpenseSubmitData) => void
  onCancel?: () => void
  isSubmitting?: boolean
}

export function ExpenseForm({ expense, onSubmit, onCancel, isSubmitting }: ExpenseFormProps) {
  const { categoriesQuery } = useCategories()
  const { activeCategoryId } = useCategoryStore()
  const { t, locale } = useTranslations()
  const defaultCurrency = getDefaultCurrencyByLocale(locale)

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors },
  } = useForm<ExpenseFormValues>({
    defaultValues: {
      amount: 0,
      currency: defaultCurrency,
      description: '',
      category_id: activeCategoryId || 0,
      date: new Date().toISOString().split('T')[0],
    },
  })

  const categories = categoriesQuery.data ?? []

  useEffect(() => {
    if (expense) {
      reset({
        amount: expense.amount,
        currency: expense.currency || defaultCurrency,
        description: expense.note,
        category_id: expense.category_id,
        date: expense.created_at.split('T')[0],
      })
    } else {
      reset({
        amount: 0,
        currency: defaultCurrency,
        description: '',
        category_id: activeCategoryId || 0,
        date: new Date().toISOString().split('T')[0],
      })
    }
  }, [expense, activeCategoryId, reset, defaultCurrency])

  // Mettre à jour la devise par défaut quand la langue change (seulement si on n'est pas en train d'éditer)
  useEffect(() => {
    if (!expense) {
      setValue('currency', defaultCurrency)
    }
  }, [locale, defaultCurrency, expense, setValue])

  // Fonction pour construire la hiérarchie des catégories
  const buildCategoryOptions = (categories: Category[]) => {
    const options: Array<{ value: number; label: string }> = []

    const addCategoryToOptions = (cats: Category[], depth = 0) => {
      cats.forEach((cat) => {
        options.push({
          value: cat.id,
          label: `${'— '.repeat(depth)}${cat.name}`,
        })
        if (cat.children && cat.children.length > 0) {
          addCategoryToOptions(cat.children, depth + 1)
        }
      })
    }

    addCategoryToOptions(categories)
    return options
  }

  const categoryOptions = buildCategoryOptions(categories)

  const handleFormSubmit = (data: ExpenseFormValues) => {
    onSubmit({
      amount: data.amount,
      currency: data.currency,
      note: data.description,
      category_id: data.category_id,
      date: data.date,
    })
  }

  const selectedCurrency = watch('currency') || 'EUR'
  const currencySymbol = getCurrencySymbol(selectedCurrency)

  return (
    <Card className="modern-card shadow-modern-lg fade-in">
      <CardHeader className="pb-4 lg:pb-6">
        <CardTitle className="flex items-center gap-3 lg:gap-4 text-xl lg:text-2xl">
          <div className="p-2 lg:p-3 bg-gradient-to-br from-emerald-400 to-green-600 rounded-2xl shadow-lg hover-lift">
            <DollarSign className="h-6 w-6 lg:h-8 lg:w-8 text-white" />
          </div>
          <div>
            <div className="text-gradient font-bold text-lg lg:text-2xl">
              {expense ? t('expenses.editButton') : t('expenses.addButton')}
            </div>
            <p className="text-muted-foreground text-xs lg:text-sm mt-1">
              {expense ? t('expenses.editSubtitle') : t('expenses.addSubtitle')}
            </p>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="p-4 lg:p-6">
        <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6 lg:space-y-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 lg:gap-8">
            <div className="space-y-2 lg:space-y-4 p-3 lg:p-6 bg-gradient-to-br from-emerald-50 to-green-100 rounded-2xl border border-emerald-200/50 min-h-[120px] flex flex-col">
              <Label htmlFor="amount" className="text-xs lg:text-sm font-semibold text-emerald-700 flex items-center gap-2">
                <div className="p-1 bg-emerald-200 rounded-md w-6 h-6 flex items-center justify-center">
                  <span className="text-emerald-600 text-xs lg:text-sm">{currencySymbol}</span>
                </div>
                {t('expenses.amount')}
              </Label>
              <div className="flex-1 flex flex-col justify-center space-y-3">
                <div className="relative">
                  <Input
                    id="amount"
                    type="number"
                    step="0.01"
                    min="0"
                    placeholder="0.00"
                    className="input-modern h-12 lg:h-14 text-base lg:text-xl font-medium pl-3 lg:pl-4 border-2 border-emerald-200 focus:border-emerald-400"
                    {...register('amount', {
                      required: t('expenses.amountRequired'),
                      min: { value: 0.01, message: t('expenses.amountPositive') },
                      valueAsNumber: true,
                    })}
                  />
                </div>
                <div className="flex items-center gap-2">
                  <Label htmlFor="currency" className="text-xs text-emerald-700 whitespace-nowrap">
                    Devise:
                  </Label>
                  <Select
                    value={selectedCurrency}
                    onValueChange={(value) => setValue('currency', value)}
                  >
                    <SelectTrigger className="h-9 text-sm border-emerald-200 focus:border-emerald-400 flex-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="max-h-[300px]">
                      {SUPPORTED_CURRENCIES.map((currency) => (
                        <SelectItem key={currency.code} value={currency.code}>
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{currency.symbol}</span>
                            <span className="text-xs text-muted-foreground">({currency.code})</span>
                            <span className="text-xs text-muted-foreground ml-1">{currency.name}</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                {errors.amount && (
                  <p className="text-xs lg:text-sm text-red-600 flex items-center gap-2 mt-2">
                    <span className="text-red-500">⚠️</span>
                    {errors.amount.message}
                  </p>
                )}
              </div>
            </div>

            <div className="space-y-2 lg:space-y-4 p-3 lg:p-6 bg-gradient-to-br from-blue-50 to-indigo-100 rounded-2xl border border-blue-200/50 min-h-[120px] flex flex-col">
              <Label htmlFor="date" className="text-xs lg:text-sm font-semibold text-blue-700 flex items-center gap-2">
                <div className="p-1 bg-blue-200 rounded-md w-6 h-6 flex items-center justify-center">
                  <Calendar className="h-3 w-3 lg:h-4 lg:w-4 text-blue-600" />
                </div>
                {t('expenses.date')}
              </Label>
              <div className="flex-1 flex flex-col justify-center">
                <div className="relative">
                  <Input
                    id="date"
                    type="date"
                    className="input-modern h-12 lg:h-14 text-base lg:text-lg pl-3 lg:pl-4 border-2 border-blue-200 focus:border-blue-400"
                    {...register('date', {
                      required: t('expenses.dateRequired'),
                    })}
                  />
                </div>
                {errors.date && (
                  <p className="text-xs lg:text-sm text-red-600 flex items-center gap-2 mt-2">
                    <span className="text-red-500">⚠️</span>
                    {errors.date.message}
                  </p>
                )}
              </div>
            </div>
          </div>

          <div className="space-y-3 lg:space-y-4 p-4 lg:p-6 bg-gradient-to-br from-purple-50 to-pink-100 rounded-2xl border border-purple-200/50">
            <Label htmlFor="category_id" className="text-xs lg:text-sm font-semibold text-purple-700 flex items-center gap-2">
              <div className="p-1 bg-purple-200 rounded-md">
                <svg className="h-3 w-3 lg:h-4 lg:w-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                </svg>
              </div>
              {t('expenses.category')}
            </Label>
            <Select
              value={watch('category_id') ? String(watch('category_id')) : ''}
              onValueChange={(value) => setValue('category_id', Number(value))}
            >
              <SelectTrigger className="input-modern h-12 lg:h-14 text-base lg:text-lg border-2 border-purple-200 focus:border-purple-400">
                <SelectValue placeholder={t('expenses.categoryPlaceholder')} />
              </SelectTrigger>
              <SelectContent className="bg-white/95 backdrop-blur-sm">
                {categoryOptions.map((option) => (
                  <SelectItem key={option.value} value={String(option.value)} className="hover:bg-purple-50">
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.category_id && (
              <p className="text-sm text-red-600 flex items-center gap-2">
                <span className="text-red-500">⚠️</span>
                {errors.category_id.message}
              </p>
            )}
          </div>

          <div className="space-y-3 lg:space-y-4 p-4 lg:p-6 bg-gradient-to-br from-amber-50 to-orange-100 rounded-2xl border border-amber-200/50">
            <Label htmlFor="description" className="text-xs lg:text-sm font-semibold text-amber-700 flex items-center gap-2">
              <div className="p-1 bg-amber-200 rounded-md">
                <svg className="h-3 w-3 lg:h-4 lg:w-4 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </div>
              {t('expenses.description')}
            </Label>
            <Textarea
              id="description"
              rows={3}
              placeholder={t('expenses.descriptionPlaceholder')}
              className="input-modern border-2 border-amber-200 focus:border-amber-400 resize-none text-sm lg:text-base"
              {...register('description')}
            />
          </div>

          <div className="flex flex-col sm:flex-row gap-3 lg:gap-4 pt-6 lg:pt-8 border-t border-gray-200">
            <Button
              type="submit"
              disabled={isSubmitting}
              className="btn-modern flex-1 h-12 lg:h-14 text-sm lg:text-lg font-semibold min-h-[44px]"
              aria-label={expense ? 'Enregistrer les modifications' : 'Créer la dépense'}
            >
              {isSubmitting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 lg:h-5 lg:w-5 border-b-2 border-white mr-2 lg:mr-3"></div>
                  {t('expenses.saving')}
                </>
              ) : (
                <>
                  <span className="mr-2 lg:mr-3 text-lg lg:text-xl">🚀</span>
                  {expense ? t('expenses.save') : t('expenses.create')}
                </>
              )}
            </Button>
            {onCancel && (
              <Button
                type="button"
                variant="outline"
                onClick={onCancel}
                className="h-12 lg:h-14 px-4 lg:px-8 text-sm lg:text-lg font-medium border-2 border-gray-300 hover:bg-gray-50 hover:border-gray-400 min-h-[44px]"
                aria-label="Annuler"
              >
                {t('expenses.cancel')}
              </Button>
            )}
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
