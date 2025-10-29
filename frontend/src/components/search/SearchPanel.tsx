'use client'

import { useState } from 'react'
import { Search, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { useTranslations } from '@/hooks/useTranslations'
import { useCategories } from '@/hooks/useCategories'
import { useExpenses } from '@/hooks/useExpenses'
import { usePagination } from '@/hooks/usePagination'
import { ExpenseCardSkeleton } from '@/components/ui/loading-states'
import { formatCurrency } from '@/lib/utils'
import { type Category } from '@/lib/api'
import { useCategoryStore } from '@/lib/store'
// ExportPanel déplacé dans l'onglet export

export interface SearchFilters {
  start_date: string
  end_date: string
  category_ids: string[]
}

interface SearchPanelProps {
  onFiltersChange: (filters: SearchFilters) => void
  onReset: () => void
}

export function SearchPanel({ onFiltersChange, onReset }: SearchPanelProps) {
  const { categoriesQuery } = useCategories()
  const { activeCategoryId } = useCategoryStore()
  const { t } = useTranslations()

  const [filters, setFilters] = useState<SearchFilters>({
    start_date: '',
    end_date: '',
    category_ids: activeCategoryId ? [String(activeCategoryId)] : [],
  })

  const [applied, setApplied] = useState(false)
  const [appliedFilters, setAppliedFilters] = useState<SearchFilters>({
    start_date: '',
    end_date: '',
    category_ids: [],
  })

  const { page, perPage, setPagination, nextPage, previousPage } = usePagination(1, 200)

  const { expensesQuery, expenses, meta } = useExpenses(
    applied
      ? {
        // On délègue uniquement la période au backend; la sélection parent->enfants est filtrée côté client
        start_date: appliedFilters.start_date || undefined,
        end_date: appliedFilters.end_date || undefined,
        page,
        per_page: perPage,
      }
      : { page, per_page: perPage }
  )

  const categories = categoriesQuery.data ?? []
  const roots = categories

  const [expanded, setExpanded] = useState<Set<number>>(new Set<number>())

  const toggleExpand = (id: number) => {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id); else next.add(id)
      return next
    })
  }

  const collectDescendantIds = (allCategories: Category[], targetId: number): Set<number> => {
    const result = new Set<number>()
    const dfs = (cats: Category[]) => {
      for (const cat of cats) {
        if (cat.id === targetId) {
          addWithChildren(cat)
        }
        if (cat.children && cat.children.length > 0) dfs(cat.children)
      }
    }
    const addWithChildren = (cat: Category) => {
      result.add(cat.id)
      if (cat.children) {
        for (const child of cat.children) addWithChildren(child)
      }
    }
    dfs(allCategories)
    return result
  }

  const formatDateForDisplay = (dateStr: string | undefined): string => {
    try {
      // Vérifier si la date existe
      if (!dateStr) {
        return 'Date non définie'
      }

      // Gérer différents formats de date
      let date: Date
      if (dateStr.includes('T')) {
        // Format ISO avec heure
        date = new Date(dateStr)
      } else if (dateStr.includes('-')) {
        // Format YYYY-MM-DD
        date = new Date(dateStr + 'T00:00:00')
      } else {
        // Autres formats
        date = new Date(dateStr)
      }

      // Vérifier si la date est valide
      if (isNaN(date.getTime())) {
        return 'Date invalide'
      }

      return date.toLocaleDateString('fr-FR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
      })
    } catch (error) {
      console.error('Erreur formatage date:', dateStr, error)
      return 'Date invalide'
    }
  }

  const categoryIdToLabel = (id: number): string => {
    // Breadth-first search across tree
    const stack: Category[] = [...categories]
    while (stack.length) {
      const node = stack.pop() as Category
      if (node.id === id) return node.name
      if (node.children && node.children.length) stack.push(...node.children)
    }
    return `#${id}`
  }

  const handleFilterChange = (key: keyof SearchFilters, value: string | string[]) => {
    const newFilters = { ...filters, [key]: value }
    setFilters(newFilters)
    onFiltersChange(newFilters)
  }

  const toggleCategory = (id: string) => {
    const set = new Set(filters.category_ids)
    if (set.has(id)) set.delete(id); else set.add(id)
    handleFilterChange('category_ids', Array.from(set))
  }

  const handleApplySearch = () => {
    setApplied(true)
    setAppliedFilters(filters)
    onFiltersChange(filters)
  }

  const handleReset = () => {
    const resetFilters = {
      start_date: '',
      end_date: '',
      category_ids: [],
    }
    setFilters(resetFilters)
    onReset()
    setApplied(false)
    setAppliedFilters(resetFilters)
  }

  const hasActiveFilters = filters.start_date || filters.end_date || filters.category_ids.length > 0

  // Filtres rapides prédéfinis
  const quickFilters = [
    {
      label: "Aujourd'hui",
      getDates: () => {
        const today = new Date()
        return {
          start_date: today.toISOString().split('T')[0],
          end_date: today.toISOString().split('T')[0]
        }
      }
    },
    {
      label: "Cette semaine",
      getDates: () => {
        const today = new Date()
        const startOfWeek = new Date(today)
        startOfWeek.setDate(today.getDate() - today.getDay())
        return {
          start_date: startOfWeek.toISOString().split('T')[0],
          end_date: today.toISOString().split('T')[0]
        }
      }
    },
    {
      label: "Ce mois",
      getDates: () => {
        const today = new Date()
        const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1)
        return {
          start_date: startOfMonth.toISOString().split('T')[0],
          end_date: today.toISOString().split('T')[0]
        }
      }
    },
    {
      label: "Mois dernier",
      getDates: () => {
        const today = new Date()
        const startOfLastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1)
        const endOfLastMonth = new Date(today.getFullYear(), today.getMonth(), 0)
        return {
          start_date: startOfLastMonth.toISOString().split('T')[0],
          end_date: endOfLastMonth.toISOString().split('T')[0]
        }
      }
    }
  ]

  const applyQuickFilter = (filter: typeof quickFilters[0]) => {
    const dates = filter.getDates()
    const newFilters = {
      ...filters,
      start_date: dates.start_date,
      end_date: dates.end_date
    }
    setFilters(newFilters)
    onFiltersChange(newFilters)
  }

  return (
    <Card className="wise-card">
      <CardHeader className="bg-green-50 rounded-t-xl">
        <CardTitle className="flex items-center gap-3 text-gray-900">
          <div className="p-2 bg-green-100 rounded-lg">
            <Search className="h-5 w-5 text-green-600" aria-hidden="true" />
          </div>
          <span className="text-xl font-semibold">{t('search.results')}</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6 p-6">
        {/* Filtres rapides */}
        <div className="space-y-2">
          <Label className="form-label text-sm font-semibold">Filtres rapides</Label>
          <div className="flex flex-wrap gap-2">
            {quickFilters.map((filter) => (
              <Button
                key={filter.label}
                variant="outline"
                size="sm"
                onClick={() => applyQuickFilter(filter)}
                className="text-xs sm:text-sm"
                aria-label={`Appliquer le filtre ${filter.label}`}
              >
                {filter.label}
              </Button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
          <div className="form-group">
            <Label htmlFor="search_start_date" className="form-label">{t('search.startDate')}</Label>
            <Input
              id="search_start_date"
              type="date"
              value={filters.start_date}
              onChange={(e) => handleFilterChange('start_date', e.target.value)}
              className="input-wise h-10 sm:h-11"
              aria-label="Date de début de recherche"
            />
          </div>

          <div className="form-group">
            <Label htmlFor="search_end_date" className="form-label">{t('search.endDate')}</Label>
            <Input
              id="search_end_date"
              type="date"
              value={filters.end_date}
              onChange={(e) => handleFilterChange('end_date', e.target.value)}
              className="input-wise h-10 sm:h-11"
              aria-label="Date de fin de recherche"
            />
          </div>
        </div>

        <div className="form-group">
          <Label className="form-label" htmlFor="category-filter">{t('search.category')}</Label>
          <div 
            id="category-filter"
            className="max-h-56 overflow-y-auto bg-gray-50 rounded-lg p-4 space-y-2"
            role="group"
            aria-label="Sélection de catégories"
          >
            <div
              className={`flex items-center gap-3 p-3 rounded-lg hover:bg-gray-100 cursor-pointer transition-all duration-200 ${filters.category_ids.length === 0 ? 'bg-green-100 border border-green-200' : ''}`}
              onClick={() => handleFilterChange('category_ids', [])}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault()
                  handleFilterChange('category_ids', [])
                }
              }}
              aria-label="Sélectionner toutes les catégories"
            >
              <input 
                type="checkbox" 
                readOnly 
                checked={filters.category_ids.length === 0} 
                className="w-4 h-4" 
                aria-label="Toutes les catégories"
              />
              <span className="text-gray-700 font-medium">{t('search.selectCategories')}</span>
            </div>
            {roots.map((cat) => (
              <CategoryTreeRow
                key={cat.id}
                node={cat}
                level={0}
                expanded={expanded}
                onToggleExpand={toggleExpand}
                selected={new Set(filters.category_ids)}
                onToggleSelected={(id) => toggleCategory(String(id))}
              />
            ))}
          </div>
        </div>


        {hasActiveFilters && (
          <div className="space-y-3 pt-2">
            <div className="flex flex-col sm:flex-row sm:items-center gap-2">
              <span className="text-sm text-muted-foreground">{t('search.button')}:</span>
              <div className="flex gap-1 flex-wrap">
                {filters.start_date && (
                  <Badge variant="secondary" className="text-xs">
                    {t('search.startDate')}: {filters.start_date}
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-4 w-4 p-0 ml-1"
                      onClick={() => handleFilterChange('start_date', '')}
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </Badge>
                )}
                {filters.end_date && (
                  <Badge variant="secondary" className="text-xs">
                    {t('search.endDate')}: {filters.end_date}
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-4 w-4 p-0 ml-1"
                      onClick={() => handleFilterChange('end_date', '')}
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </Badge>
                )}
                {filters.category_ids.length > 0 && (
                  <Badge variant="secondary" className="text-xs">
                    {filters.category_ids.length} {t('search.category')}
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-4 w-4 p-0 ml-1"
                      onClick={() => handleFilterChange('category_ids', [])}
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </Badge>
                )}
              </div>
            </div>
            <div className="flex flex-col sm:flex-row gap-2">
              <Button variant="ghost" size="sm" onClick={handleReset} className="btn-wise-secondary flex-1 sm:flex-none">
                {t('search.reset')}
              </Button>
              <Button size="sm" onClick={handleApplySearch} className="btn-wise flex-1 sm:flex-none">
                {t('search.button')}
              </Button>
            </div>
          </div>
        )}

        <div className="pt-4 border-t">
          {!applied ? (
            <div className="text-sm text-muted-foreground">{t('search.results')}</div>
          ) : expensesQuery.isLoading ? (
            <div className="space-y-4">
              <div className="text-sm text-muted-foreground mb-4">Chargement des résultats...</div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
                  <ExpenseCardSkeleton key={i} />
                ))}
              </div>
            </div>
          ) : expensesQuery.isError ? (
            <div className="text-sm text-destructive">{t('errors.validationFailed')}</div>
          ) : expenses && expenses.length > 0 ? (
            (() => {
              const filteredExpenses = expenses.filter((e) => {
                if (!appliedFilters.category_ids || appliedFilters.category_ids.length === 0) return true
                const selected = new Set<number>()
                for (const id of appliedFilters.category_ids) {
                  collectDescendantIds(categories, Number(id)).forEach((v) => selected.add(v))
                }
                return selected.has(e.category_id)
              })
              
              // Grouper les totaux par devise
              const totalsByCurrency = filteredExpenses.reduce((acc, expense) => {
                const currency = expense.currency || 'EUR'
                acc[currency] = (acc[currency] || 0) + expense.amount
                return acc
              }, {} as Record<string, number>)

              return (
                <div className="space-y-2">
                  <div className="flex flex-col gap-2 bg-green-50 p-3 rounded-lg border border-green-200">
                    <div className="text-sm text-muted-foreground">
                      {t('search.results')} ({filteredExpenses.length})
                    </div>
                    <div className="flex flex-col gap-1">
                      {Object.entries(totalsByCurrency).map(([currency, total]) => (
                        <div key={currency} className="text-lg font-bold text-green-700">
                          {t('summary.total')} ({currency}): {formatCurrency(Math.round(total), currency)}
                        </div>
                      ))}
                      {Object.keys(totalsByCurrency).length > 1 && (
                        <div className="text-xs text-amber-600 mt-1">
                          ⚠️ Multiple devises détectées
                        </div>
                      )}
                    </div>
                  </div>
                  {meta && (
                    <div className="flex justify-between items-center text-xs text-muted-foreground">
                      <span>
                        {t('summary.month')} {meta.page} / {Math.max(1, Math.ceil(meta.total / meta.per_page))}
                      </span>
                      <span>{meta.total} {t('expenses.title')}</span>
                    </div>
                  )}
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    {filteredExpenses.map((e) => (
                      <Card key={e.id} className="wise-card">
                        <CardContent className="p-4">
                          <div className="space-y-4">
                            {/* En-tête avec catégorie */}
                            <div className="flex items-center justify-between">
                              <Badge className="badge-wise">
                                {categoryIdToLabel(e.category_id)}
                              </Badge>
                            </div>

                            {/* Montant centré et proéminent */}
                            <div className="text-center">
                              <div className="font-bold text-lg text-gray-900 break-all">
                                {formatCurrency(Math.round(e.amount), e.currency || 'EUR')}
                              </div>
                              {e.currency && e.currency !== 'EUR' && (
                                <div className="text-xs text-muted-foreground mt-1">
                                  {e.currency}
                                </div>
                              )}
                            </div>

                            {/* Informations secondaires */}
                            <div className="space-y-3 text-xs">
                              <div className="bg-gray-50 rounded-lg p-3">
                                <div className="text-gray-900 font-medium">
                                  {formatDateForDisplay(e.created_at)}
                                </div>
                              </div>

                              {e.note && (
                                <div className="bg-gray-50 rounded-lg p-3">
                                  <div className="text-gray-900 leading-relaxed">
                                    {e.note}
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                  {meta && (
                    <div className="flex justify-between items-center text-xs text-muted-foreground">
                      <span>
                        Page {meta.page} / {Math.max(1, Math.ceil(meta.total / meta.per_page))}
                      </span>
                      <span>{meta.total} dépenses au total</span>
                    </div>
                  )}
                </div>
              )
            })()
          ) : (
            <div className="text-sm text-muted-foreground">Aucun résultat trouvé</div>
          )}
          {/* Export déplacé dans l'onglet dédié */}
        </div>
        {meta && (
          <div className="flex justify-between items-center pt-4 border-t">
            <Button variant="ghost" size="sm" onClick={previousPage} disabled={!meta.has_previous}>
              Précédent
            </Button>
            <span className="text-xs text-muted-foreground">
              Page {meta.page} / {Math.max(1, Math.ceil(meta.total / meta.per_page))}
            </span>
            <Button variant="ghost" size="sm" onClick={nextPage} disabled={!meta.has_next}>
              Suivant
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function CategoryTreeRow({
  node,
  level,
  expanded,
  onToggleExpand,
  selected,
  onToggleSelected,
}: {
  node: Category
  level: number
  expanded: Set<number>
  onToggleExpand: (id: number) => void
  selected: Set<string>
  onToggleSelected: (id: number) => void
}) {
  const hasChildren = !!node.children && node.children.length > 0
  const isExpanded = expanded.has(node.id)
  return (
    <div>
      <div
        className="flex items-center gap-2 p-2 rounded hover:bg-accent/40"
        style={{ marginLeft: `${level * 16}px` }}
      >
        {hasChildren ? (
          <button
            className="h-5 w-5 text-muted-foreground"
            onClick={(e) => {
              e.preventDefault()
              onToggleExpand(node.id)
            }}
            aria-label={isExpanded ? 'Collapse' : 'Expand'}
          >
            {isExpanded ? '▾' : '▸'}
          </button>
        ) : (
          <span className="h-5 w-5" />
        )}
        <input
          type="checkbox"
          readOnly
          checked={selected.has(String(node.id))}
          onClick={(e) => {
            e.preventDefault()
            onToggleSelected(node.id)
          }}
        />
        <button
          className="text-left truncate flex-1"
          onClick={(e) => {
            e.preventDefault()
            onToggleSelected(node.id)
          }}
        >
          {node.name}
        </button>
      </div>
      {hasChildren && isExpanded && (
        <div>
          {node.children!.map((child) => (
            <CategoryTreeRow
              key={child.id}
              node={child}
              level={level + 1}
              expanded={expanded}
              onToggleExpand={onToggleExpand}
              selected={selected}
              onToggleSelected={onToggleSelected}
            />
          ))}
        </div>
      )}
    </div>
  )
}
