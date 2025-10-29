'use client'

import { useMemo, useState } from 'react'
import { ChevronRight, ChevronDown, Edit, Trash2, MoreHorizontal, Search, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useTranslations } from '@/hooks/useTranslations'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useCategories } from '@/hooks/useCategories'
import { useCategoryStore } from '@/lib/store'
import { type Category } from '@/lib/api'
import { CategoryListSkeleton } from '@/components/ui/loading-states'
import { Input } from '@/components/ui/input'
import { toast } from 'sonner'
import React from 'react'

interface CategoryNodeProps {
  category: Category
  level: number
  onSelect: (id: number) => void
  onEdit: (category: Category) => void
  onDelete: (category: Category) => void
  selectedId?: number | null
}

function CategoryNode({ category, level, onSelect, onEdit, onDelete, selectedId }: CategoryNodeProps) {
  const [isExpanded, setIsExpanded] = useState(level === 0)
  const { t } = useTranslations()
  const hasChildren = category.children && category.children.length > 0
  const isSelected = selectedId === category.id

  return (
    <div className="w-full">
      <div
        className={`group flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all duration-200 hover:bg-accent/50 hover:shadow-sm ${isSelected ? 'bg-primary/5 border border-primary/20 shadow-sm' : 'hover:border-border'
          }`}
        style={{ marginLeft: `${level * 12}px` }}
        onClick={() => onSelect(category.id)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            onSelect(category.id)
          }
        }}
        aria-label={`Sélectionner la catégorie ${category.name}`}
        aria-expanded={hasChildren ? isExpanded : undefined}
      >
        {hasChildren ? (
          <Button
            variant="ghost"
            size="sm"
            className="h-6 w-6 p-0 hover:bg-accent/80"
            onClick={(e) => {
              e.stopPropagation()
              setIsExpanded(!isExpanded)
            }}
            aria-label={isExpanded ? `Réduire ${category.name}` : `Développer ${category.name}`}
            aria-expanded={isExpanded}
          >
            {isExpanded ? (
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
            )}
          </Button>
        ) : (
          <div className="h-6 w-6 flex items-center justify-center">
            <div className="h-2 w-2 rounded-full bg-muted-foreground/30" />
          </div>
        )}

        <div className="flex-1 min-w-0">
          <div
            className={`font-medium text-sm truncate ${isSelected ? 'text-primary' : 'text-foreground'}`}
            onClick={(e) => {
              if (hasChildren) {
                e.stopPropagation()
                setIsExpanded(!isExpanded)
              }
            }}
          >
            {category.name}
          </div>
          {category.description && (
            <div className="text-xs text-muted-foreground truncate mt-0.5">
              {category.description}
            </div>
          )}
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity min-w-[44px] min-h-[44px]"
              onClick={(e) => e.stopPropagation()}
              aria-label={`Menu options pour ${category.name}`}
            >
              <MoreHorizontal className="h-4 w-4" aria-hidden="true" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            <DropdownMenuItem onClick={() => onEdit(category)} className="cursor-pointer">
              <Edit className="mr-2 h-4 w-4" />
              {t('categories.editButton')}
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={() => onDelete(category)}
              className="text-destructive cursor-pointer"
            >
              <Trash2 className="mr-2 h-4 w-4" />
              {t('categories.deleteButton')}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {hasChildren && isExpanded && (
        <div className="ml-6 mt-1">
          {category.children?.map((child) => (
            <CategoryNode
              key={child.id}
              category={child}
              level={level + 1}
              onSelect={onSelect}
              onEdit={onEdit}
              onDelete={onDelete}
              selectedId={selectedId}
            />
          ))}
        </div>
      )}
    </div>
  )
}

interface CategoryListProps {
  onEditCategory?: (category: Category) => void
  showHeader?: boolean
}

export function CategoryList({ onEditCategory, showHeader = true }: CategoryListProps) {
  const { categoriesQuery, deleteCategory } = useCategories()
  const { activeCategoryId, setActiveCategoryId } = useCategoryStore()
  const [searchQuery, setSearchQuery] = useState('')
  const categories = categoriesQuery.data ?? []
  
  // Fonction de recherche récursive
  const filterCategories = (cats: Category[], query: string): Category[] => {
    if (!query.trim()) return cats
    
    const lowerQuery = query.toLowerCase()
    return cats
      .map(cat => {
        const matches = cat.name.toLowerCase().includes(lowerQuery) ||
          cat.description?.toLowerCase().includes(lowerQuery)
        const filteredChildren = cat.children ? filterCategories(cat.children, query) : []
        
        if (matches || filteredChildren.length > 0) {
          return {
            ...cat,
            children: filteredChildren.length > 0 ? filteredChildren : cat.children
          }
        }
        return null
      })
      .filter((cat): cat is Category => cat !== null)
  }
  
  const filteredCategories = useMemo(() => {
    return filterCategories(categories, searchQuery)
  }, [categories, searchQuery])
  
  const roots = filteredCategories
  const totalCount = useMemo(() => {
    const dfs = (nodes: Category[]): number =>
      nodes.reduce((acc, n) => acc + 1 + (n.children ? dfs(n.children as Category[]) : 0), 0)
    return dfs(categories) // Total avant filtrage
  }, [categories])

  const handleDelete = async (category: Category) => {
    const label = category.full_path ?? category.name
    const toastId = toast.loading('Suppression en cours...')
    
    try {
      await deleteCategory.mutateAsync(category.id)
      if (category.id === activeCategoryId) {
        setActiveCategoryId(null)
      }
      toast.success('Catégorie supprimée', {
        id: toastId,
        description: `La catégorie "${label}" a été supprimée avec succès`
      })
    } catch (error: any) {
      const errorMessage = error?.response?.data?.detail || 'Erreur lors de la suppression'
      toast.error('Erreur de suppression', {
        id: toastId,
        description: errorMessage
      })
      console.error('Erreur lors de la suppression:', error)
    }
  }

  const handleEdit = (category: Category) => {
    if (onEditCategory) {
      onEditCategory(category)
    }
  }

  if (categoriesQuery.isLoading) {
    return <CategoryListSkeleton />
  }

  if (categoriesQuery.isError) {
    return (
      <Card className="h-full">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <CardTitle className="text-lg font-semibold">Catégories</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-64">
          <div className="text-center text-destructive">
            <div className="text-4xl mb-2">⚠️</div>
            <div className="font-medium">Erreur</div>
            <div className="text-sm text-muted-foreground mt-1">
              Erreur
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="h-full">
      {showHeader && (
        <CardHeader className="pb-4">
          <div>
            <CardTitle className="text-lg font-semibold">Catégories</CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              {`Total : ${totalCount} catégories`}
            </p>
          </div>
        </CardHeader>
      )}
      <CardContent className="p-0">
        {/* Barre de recherche */}
        {categories.length > 0 && (
          <div className="p-2 border-b">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                type="text"
                placeholder="Rechercher une catégorie..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 pr-9 h-9 text-sm"
                aria-label="Rechercher dans les catégories"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 p-1 hover:bg-accent rounded"
                  aria-label="Effacer la recherche"
                >
                  <X className="h-4 w-4 text-muted-foreground" />
                </button>
              )}
            </div>
            {searchQuery && (
              <p className="text-xs text-muted-foreground mt-2 px-1">
                {roots.length > 0 
                  ? `${roots.length} résultat${roots.length > 1 ? 's' : ''} trouvé${roots.length > 1 ? 's' : ''}`
                  : 'Aucun résultat'}
              </p>
            )}
          </div>
        )}
        {categories.length === 0 ? (
          <div className="p-8 text-center">
            <div className="text-4xl mb-3">📂</div>
            <div className="text-muted-foreground font-medium mb-1">
              Aucune catégorie
            </div>
            <div className="text-sm text-muted-foreground">
              Créez votre première catégorie pour commencer
            </div>
          </div>
        ) : (
          <div className="max-h-96 overflow-y-auto">
            <div className="p-2 space-y-1">
              {roots.map((category) => (
                <CategoryNode
                  key={category.id}
                  category={category}
                  level={0}
                  onSelect={setActiveCategoryId}
                  onEdit={handleEdit}
                  onDelete={handleDelete}
                  selectedId={activeCategoryId}
                />
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
