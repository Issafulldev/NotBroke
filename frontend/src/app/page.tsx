'use client'

import { useState } from 'react'
import { QueryProvider } from '@/lib/query-client'
import { useTranslations } from '@/hooks/useTranslations'
import { Layout } from '@/components/layout/Layout'
import { CategoryList } from '@/components/categories/CategoryList'
import { CategoryForm, type CategorySubmitData } from '@/components/categories/CategoryForm'
import { CategoryModal } from '@/components/categories/CategoryModal'
import { ExpenseForm, type ExpenseSubmitData } from '@/components/expenses/ExpenseForm'
import { MonthlySummary } from '@/components/summary/MonthlySummary'
import { SearchPanel, type SearchFilters } from '@/components/search/SearchPanel'
import { ExportPanel } from '@/components/export/ExportPanel'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { ChevronDown, ChevronRight } from 'lucide-react'
import { toast } from 'sonner'
import { formatCurrency } from '@/lib/utils'
import { useCategories } from '@/hooks/useCategories'
import { useExpenses } from '@/hooks/useExpenses'
import { type Category, type Expense } from '@/lib/api'

function AppContent() {
  const { t } = useTranslations()
  const { createCategory, updateCategory } = useCategories()
  const { createExpense, updateExpense } = useExpenses()

  const [editingCategory, setEditingCategory] = useState<Category | null>(null)
  const [editingExpense, setEditingExpense] = useState<Expense | null>(null)
  const [activeTab, setActiveTab] = useState<'create' | 'search' | 'export'>('create')
  const [showCategoriesMobile, setShowCategoriesMobile] = useState(false)
  const [showSummaryMobile, setShowSummaryMobile] = useState(false)
  const [showCategoriesDesktop, setShowCategoriesDesktop] = useState(false)

  const handleCategorySubmit = async (data: Omit<CategorySubmitData, 'id'>) => {
    const isEditing = !!editingCategory
    const toastId = toast.loading(isEditing ? 'Modification en cours...' : 'Création en cours...')
    
    try {
      if (editingCategory) {
        await updateCategory.mutateAsync({ id: editingCategory.id, payload: data })
        setEditingCategory(null)
        toast.success('Catégorie modifiée', {
          id: toastId,
          description: `La catégorie "${data.name}" a été modifiée avec succès`
        })
      } else {
        await createCategory.mutateAsync(data)
        toast.success('Catégorie créée', {
          id: toastId,
          description: `La catégorie "${data.name}" a été créée avec succès`
        })
      }
    } catch (error: any) {
      const errorMessage = error?.response?.data?.detail || 'Erreur lors de l\'opération'
      toast.error('Erreur', {
        id: toastId,
        description: errorMessage
      })
      console.error('Erreur catégorie:', error)
    }
  }

  const handleExpenseSubmit = async (data: ExpenseSubmitData) => {
    const isEditing = !!editingExpense
    const toastId = toast.loading(isEditing ? 'Modification en cours...' : 'Création en cours...')
    
    try {
      if (editingExpense) {
        await updateExpense.mutateAsync({ id: editingExpense.id, payload: data })
        setEditingExpense(null)
        toast.success('Dépense modifiée', {
          id: toastId,
          description: `La dépense de ${formatCurrency(data.amount, data.currency)} a été modifiée avec succès`
        })
      } else {
        await createExpense.mutateAsync(data)
        toast.success('Dépense ajoutée', {
          id: toastId,
          description: `La dépense de ${formatCurrency(data.amount, data.currency)} a été ajoutée avec succès`
        })
      }
    } catch (error: any) {
      const errorMessage = error?.response?.data?.detail || 'Erreur lors de l\'opération'
      toast.error('Erreur', {
        id: toastId,
        description: errorMessage
      })
      console.error('Erreur dépense:', error)
    }
  }

  const handleSearchFiltersChange = (filters: SearchFilters) => {
    // Hook can later fetch filtered expenses; for now we just log.
    console.debug('Filtres de recherche mis à jour', filters)
  }

  const handleSearchReset = () => {
    console.debug('Filtres de recherche réinitialisés')
  }

  return (
    <Layout
      sidebar={
        <div className="space-y-4">
          {/* Catégories - Desktop collapsible */}
          <Card className="hidden lg:block bg-white/60 backdrop-blur-sm border border-white/20 shadow-lg">
            <Button
              variant="ghost"
              className="w-full justify-between p-4 text-left"
              onClick={() => setShowCategoriesDesktop(!showCategoriesDesktop)}
            >
              <span className="font-semibold text-gray-900">{t('categories.title')}</span>
              {showCategoriesDesktop ? (
                <ChevronDown className="h-5 w-5 text-gray-500" />
              ) : (
                <ChevronRight className="h-5 w-5 text-gray-500" />
              )}
            </Button>
            {showCategoriesDesktop && (
              <div className="px-4 pb-4 border-t border-gray-200">
                <div className="pt-4 space-y-4">
                  <CategoryModal
                    onSubmit={handleCategorySubmit}
                    isSubmitting={createCategory.isPending}
                  />
                  <CategoryList onEditCategory={setEditingCategory} showHeader={false} />
                  {editingCategory && (
                    <CategoryForm
                      category={editingCategory}
                      onSubmit={handleCategorySubmit}
                      onCancel={() => setEditingCategory(null)}
                      isSubmitting={createCategory.isPending || updateCategory.isPending}
                    />
                  )}
                </div>
              </div>
            )}
          </Card>
        </div>
      }
      main={
        <div className="space-y-8 fade-in">
          <div className="text-center space-y-4">
            <div className="inline-flex items-center gap-4 px-8 py-6 bg-white rounded-2xl shadow-wise-lg border border-gray-200">
              <div className="p-3 bg-green-100 rounded-xl">
                <span className="text-3xl">💰</span>
              </div>
              <div className="text-left flex-1">
                <h1 className="notbroke-title">{t('dashboard.title')}</h1>
                <p className="text-gray-600 text-base">
                  {t('dashboard.subtitle')}
                </p>
              </div>
            </div>
          </div>

          {/* Sections collapsables mobile uniquement */}
          <div className="lg:hidden space-y-4">
            {/* Section Catégories mobile */}
            <Card className="bg-white/60 backdrop-blur-sm border border-white/20 shadow-lg">
              <Button
                variant="ghost"
                className="w-full justify-between p-4 text-left"
                onClick={() => setShowCategoriesMobile(!showCategoriesMobile)}
              >
                <span className="font-semibold text-gray-900">{t('categories.title')}</span>
                {showCategoriesMobile ? (
                  <ChevronDown className="h-5 w-5 text-gray-500" />
                ) : (
                  <ChevronRight className="h-5 w-5 text-gray-500" />
                )}
              </Button>
              {showCategoriesMobile && (
                <div className="px-4 pb-4 border-t border-gray-200">
                  <div className="pt-4 space-y-4">
                    <CategoryModal
                      onSubmit={handleCategorySubmit}
                      isSubmitting={createCategory.isPending}
                    />
                    <CategoryList onEditCategory={setEditingCategory} showHeader={false} />
                    {editingCategory && (
                      <CategoryForm
                        category={editingCategory}
                        onSubmit={handleCategorySubmit}
                        onCancel={() => setEditingCategory(null)}
                        isSubmitting={createCategory.isPending || updateCategory.isPending}
                      />
                    )}
                  </div>
                </div>
              )}
            </Card>

            {/* Section Résumé mobile */}
            <Card className="bg-white/60 backdrop-blur-sm border border-white/20 shadow-lg">
              <Button
                variant="ghost"
                className="w-full justify-between p-4 text-left"
                onClick={() => setShowSummaryMobile(!showSummaryMobile)}
              >
                <span className="font-semibold text-gray-900">{t('summary.title')}</span>
                {showSummaryMobile ? (
                  <ChevronDown className="h-5 w-5 text-gray-500" />
                ) : (
                  <ChevronRight className="h-5 w-5 text-gray-500" />
                )}
              </Button>
              {showSummaryMobile && (
                <div className="px-4 pb-4 border-t border-gray-200">
                  <div className="pt-4">
                    <MonthlySummary />
                  </div>
                </div>
              )}
            </Card>
          </div>

          {/* Onglets Wise-style */}
          <div className="flex justify-center">
            <div className="inline-flex bg-white p-1 lg:p-2 rounded-xl shadow-wise border border-gray-200 w-full max-w-md lg:max-w-none" role="tablist" aria-label="Navigation principale">
              <Button
                variant={activeTab === 'create' ? 'default' : 'ghost'}
                size="lg"
                onClick={() => setActiveTab('create')}
                role="tab"
                aria-selected={activeTab === 'create'}
                aria-controls="create-panel"
                className={`flex-1 lg:flex-none px-3 lg:px-6 py-2 lg:py-3 rounded-lg font-medium transition-all duration-200 text-sm lg:text-base min-h-[44px] ${activeTab === 'create'
                  ? 'bg-green-600 text-white shadow-wise'
                  : 'hover:bg-green-50 hover:text-green-700 text-gray-700'
                  }`}
              >
                {t('dashboard.tabs.create')}
              </Button>
              <Button
                variant={activeTab === 'search' ? 'default' : 'ghost'}
                size="lg"
                onClick={() => setActiveTab('search')}
                role="tab"
                aria-selected={activeTab === 'search'}
                aria-controls="search-panel"
                className={`flex-1 lg:flex-none px-3 lg:px-6 py-2 lg:py-3 rounded-lg font-medium transition-all duration-200 text-sm lg:text-base min-h-[44px] ${activeTab === 'search'
                  ? 'bg-green-600 text-white shadow-wise'
                  : 'hover:bg-green-50 hover:text-green-700 text-gray-700'
                  }`}
              >
                {t('dashboard.tabs.search')}
              </Button>
              <Button
                variant={activeTab === 'export' ? 'default' : 'ghost'}
                size="lg"
                onClick={() => setActiveTab('export')}
                role="tab"
                aria-selected={activeTab === 'export'}
                aria-controls="export-panel"
                className={`flex-1 lg:flex-none px-3 lg:px-6 py-2 lg:py-3 rounded-lg font-medium transition-all duration-200 text-sm lg:text-base min-h-[44px] ${activeTab === 'export'
                  ? 'bg-green-600 text-white shadow-wise'
                  : 'hover:bg-green-50 hover:text-green-700 text-gray-700'
                  }`}
              >
                {t('dashboard.tabs.export')}
              </Button>
            </div>
          </div>

          {activeTab === 'create' ? (
            <div className="space-y-6" id="create-panel" role="tabpanel" aria-labelledby="create-tab">
              <ExpenseForm
                expense={editingExpense}
                onSubmit={handleExpenseSubmit}
                onCancel={() => setEditingExpense(null)}
                isSubmitting={createExpense.isPending || updateExpense.isPending}
              />
            </div>
          ) : activeTab === 'search' ? (
            <div id="search-panel" role="tabpanel" aria-labelledby="search-tab">
              <SearchPanel
                onFiltersChange={handleSearchFiltersChange}
                onReset={handleSearchReset}
              />
            </div>
          ) : (
            <div className="space-y-4" id="export-panel" role="tabpanel" aria-labelledby="export-tab">
              <Card className="p-4">
                <div className="text-sm text-muted-foreground">
                  {t('dashboard.hint.export')}
                </div>
              </Card>
              <ExportPanel />
            </div>
          )}
        </div>
      }
      summary={
        <MonthlySummary />
      }
    />
  )
}

export default function Home() {
  return (
    <QueryProvider>
      <AppContent />
    </QueryProvider>
  )
}
