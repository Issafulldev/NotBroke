'use client'

import { useState } from 'react'
import { TrendingUp, ChevronDown, ChevronRight } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useTranslations } from '@/hooks/useTranslations'
import { useMonthlySummary, type SummaryFilters } from '@/hooks/useSummary'
import { useCategories } from '@/hooks/useCategories'
import { formatDateOnly, formatCurrency } from '@/lib/utils'
import { SummarySkeleton } from '@/components/ui/loading-states'
import type { Category } from '@/lib/api'

interface MonthlySummaryProps {
  filters?: SummaryFilters
}

export function MonthlySummary({ filters }: MonthlySummaryProps) {
  const { data: summary, isLoading, isError } = useMonthlySummary(filters)
  const { data: categories = [] } = useCategories()
  const { t } = useTranslations()
  const [expandedCategories, setExpandedCategories] = useState<Set<number>>(new Set())

  const toggleCategory = (categoryId: number) => {
    setExpandedCategories(prev => {
      const newSet = new Set(prev)
      if (newSet.has(categoryId)) {
        newSet.delete(categoryId)
      } else {
        newSet.add(categoryId)
      }
      return newSet
    })
  }

  // Regrouper les totaux par catégorie mère
  const getGroupedCategoryTotals = () => {
    const grouped: Record<string, number> = {}

    // Regrouper les totaux par catégorie mère
    Object.entries(summary?.category_totals || {}).forEach(([categoryPath, amount]) => {
      // Extraire le nom de la catégorie mère (première partie avant " /")
      const parentCategory = categoryPath.split(' /')[0]
      grouped[parentCategory] = (grouped[parentCategory] || 0) + amount
    })

    return grouped
  }

  const groupedTotals = getGroupedCategoryTotals()

  // Obtenir les enfants d'une catégorie mère
  const getCategoryChildren = (parentName: string) => {
    return Object.entries(summary?.category_totals || {})
      .filter(([categoryPath]) => categoryPath.startsWith(parentName + ' /'))
      .map(([categoryPath, amount]) => ({
        name: categoryPath.split(' /')[1], // Nom de l'enfant
        fullPath: categoryPath,
        amount
      }))
      .sort((a, b) => b.amount - a.amount)
  }

  // Composant pour afficher une catégorie avec ses enfants
  const CategoryItem = ({ categoryName, totalAmount }: { categoryName: string; totalAmount: number }) => {
    const children = getCategoryChildren(categoryName)
    const hasChildren = children.length > 0
    const isExpanded = expandedCategories.has(categoryName)
    const percentage = summary?.total ? ((totalAmount / summary.total) * 100).toFixed(1) : '0'

    return (
      <div className="space-y-1">
        <div
          className="group flex items-center gap-3 p-4 rounded-lg cursor-pointer transition-all duration-200 hover:bg-accent/50 hover:shadow-sm hover:border-border border"
          onClick={() => hasChildren && toggleCategory(categoryName)}
        >
          {hasChildren ? (
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0 hover:bg-accent/80"
              onClick={(e) => {
                e.stopPropagation()
                toggleCategory(categoryName)
              }}
            >
              {isExpanded ? (
                <ChevronDown className="h-4 w-4 text-muted-foreground" />
              ) : (
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
              )}
            </Button>
          ) : (
            <div className="h-6 w-6 flex items-center justify-center">
              <div className="h-2 w-2 rounded-full bg-green-500" />
            </div>
          )}

          <div className="flex-1 min-w-0">
            <div className="font-medium text-sm truncate text-foreground">
              {categoryName}
            </div>
          </div>

          <div className="text-right">
            <span className="font-bold text-lg">
              {formatCurrency(Math.round(totalAmount), 'EUR')}
            </span>
            <div className="text-xs text-muted-foreground">
              {percentage}% {t('summary.percentOfTotal')}
            </div>
          </div>
        </div>

        {hasChildren && isExpanded && (
          <div className="ml-6 space-y-2">
            {children.map((child) => (
              <div
                key={child.fullPath}
                className="flex items-center justify-between p-3 rounded-lg bg-muted/20 border hover:bg-muted/30 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="h-6 w-6 flex items-center justify-center">
                    <div className="h-2 w-2 rounded-full bg-green-500" />
                  </div>
                  <div>
                    <Badge variant="outline" className="font-medium">
                      {child.name}
                    </Badge>
                  </div>
                </div>
                <div className="text-right">
                  <span className="font-bold text-lg">
                    {formatCurrency(Math.round(child.amount), 'EUR')}
                  </span>
                  <div className="text-xs text-muted-foreground">
                    {((child.amount / summary.total) * 100).toFixed(1)}% {t('summary.percentOfTotal')}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  if (isLoading) {
    return <SummarySkeleton />
  }

  if (isError) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{t('summary.title')}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center text-destructive">
            {t('errors.validationFailed')}
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!summary) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{t('summary.title')}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center text-muted-foreground">
            {t('summary.noData')}
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="shadow-lg">
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-3 text-xl">
          <div className="p-2 bg-blue-100 rounded-lg">
            <TrendingUp className="h-6 w-6 text-blue-600" />
          </div>
          {t('summary.title')}
        </CardTitle>
        <div className="text-sm text-muted-foreground">
          {formatDateOnly(summary.start_date || '')} → {formatDateOnly(summary.end_date || '')}
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Total général */}
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-xl border">
          <div>
            <p className="text-sm font-medium text-muted-foreground mb-1">
              {t('summary.total')}
            </p>
              <p className="text-3xl font-bold text-blue-900">
                {formatCurrency(Math.round(summary.total), 'EUR')}
              </p>
          </div>
        </div>

        {/* Détail par catégorie avec collapse */}
        {Object.keys(groupedTotals).length > 0 && (
          <div className="space-y-4">
            <h4 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
              {t('summary.byCategory')}
            </h4>
            <div className="space-y-2">
              {Object.entries(groupedTotals)
                .sort(([, a], [, b]) => b - a)
                .map(([categoryName, amount]) => (
                  <CategoryItem
                    key={categoryName}
                    categoryName={categoryName}
                    totalAmount={amount}
                  />
                ))}
            </div>
          </div>
        )}

        {/* Statistiques */}
        {Object.keys(summary.category_totals).length > 0 && (
          <div className="space-y-4 pt-4 border-t">
            <h4 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
              {t('summary.statistics')}
            </h4>
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-4 rounded-lg bg-gradient-to-br from-green-50 to-emerald-50 border">
                <div className="text-2xl font-bold text-green-700 mb-1">
                  {Object.keys(summary.category_totals).length}
                </div>
                <div className="text-sm text-green-600 font-medium">
                  {t('summary.categoriesUsed')}
                </div>
              </div>
              <div className="text-center p-4 rounded-lg bg-gradient-to-br from-purple-50 to-violet-50 border">
                <div className="text-lg font-bold text-purple-700 mb-1">
                  {formatCurrency(Math.round(summary.total / Math.max(Object.keys(summary.category_totals).length, 1)), 'EUR')}
                </div>
                <div className="text-sm text-purple-600 font-medium">
                  {t('summary.averagePerCategory')}
                </div>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
