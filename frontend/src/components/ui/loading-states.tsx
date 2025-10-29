'use client'

import { Skeleton } from './skeleton'
import { Card, CardContent, CardHeader } from './card'

export function ExpenseCardSkeleton() {
  return (
    <Card className="wise-card">
      <CardContent className="p-4">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <Skeleton className="h-6 w-20" />
          </div>
          <div className="text-center">
            <Skeleton className="h-8 w-24 mx-auto" />
          </div>
          <div className="space-y-3">
            <Skeleton className="h-16 w-full rounded-lg" />
            <Skeleton className="h-16 w-full rounded-lg" />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export function CategoryListSkeleton() {
  return (
    <Card className="h-full">
      <CardHeader className="pb-4">
        <Skeleton className="h-6 w-32" />
        <Skeleton className="h-4 w-24 mt-2" />
      </CardHeader>
      <CardContent className="p-0">
        <div className="p-2 space-y-2">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-12 w-full rounded-lg" />
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

export function SummarySkeleton() {
  return (
    <Card className="shadow-lg">
      <CardHeader className="pb-4">
        <Skeleton className="h-6 w-40" />
        <Skeleton className="h-4 w-48 mt-2" />
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-xl border">
          <Skeleton className="h-12 w-32" />
        </div>
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-16 w-full rounded-lg" />
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

export function ExpenseFormSkeleton() {
  return (
    <Card className="modern-card shadow-modern-lg">
      <CardHeader className="pb-4 lg:pb-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-4 w-64 mt-2" />
      </CardHeader>
      <CardContent className="p-4 lg:p-6 space-y-6">
        <div className="grid grid-cols-2 gap-3 lg:gap-8">
          <Skeleton className="h-32 rounded-2xl" />
          <Skeleton className="h-32 rounded-2xl" />
        </div>
        <Skeleton className="h-24 rounded-2xl" />
        <Skeleton className="h-24 rounded-2xl" />
        <Skeleton className="h-12 w-full" />
      </CardContent>
    </Card>
  )
}

