'use client'

import { useState } from 'react'
import { Download, FileText, FileSpreadsheet } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { useTranslations } from '@/hooks/useTranslations'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { useCategories } from '@/hooks/useCategories'
import { api } from '@/lib/api'

interface ExportParams {
  format: 'csv' | 'xlsx'
  start_date: string
  end_date: string
  category_id?: number
}

export function ExportPanel() {
  const { t } = useTranslations()
  const [format, setFormat] = useState<'csv' | 'xlsx'>('csv')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [isExporting, setIsExporting] = useState(false)

  const { categoriesQuery } = useCategories()

  const categories = categoriesQuery.data ?? []

  const handleExport = async () => {
    if (!startDate || !endDate) {
      alert(t('export.selectPeriod'))
      return
    }

    if (new Date(startDate) > new Date(endDate)) {
      alert(t('export.invalidDates'))
      return
    }

    setIsExporting(true)

    try {
      const params: ExportParams = {
        format,
        start_date: startDate,
        end_date: endDate,
        ...(categoryId ? { category_id: parseInt(categoryId, 10) } : {}),
      }

      const response = await api.get('/expenses/export', {
        params,
        responseType: 'blob',
      })

      // Créer un lien de téléchargement
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url

      // Récupérer le nom du fichier depuis les headers
      const contentDisposition = response.headers['content-disposition']
      const filename = contentDisposition
        ? contentDisposition.split('filename=')[1].replace(/"/g, '')
        : `expenses.${format}`

      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error("Erreur lors de l'export:", error)
      alert(t('export.error'))
    } finally {
      setIsExporting(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Download className="h-5 w-5" />
          {t('export.title')}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="start_date">{t('export.startDate')}</Label>
            <Input
              id="start_date"
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="end_date">{t('export.endDate')}</Label>
            <Input
              id="end_date"
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="category">{t('export.category')}</Label>
          <Select value={categoryId || 'all'} onValueChange={(v) => setCategoryId(v === 'all' ? '' : v)}>
            <SelectTrigger>
              <SelectValue placeholder={t('export.category')} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t('export.category')}</SelectItem>
              {categories.map((category) => (
                <SelectItem key={category.id} value={String(category.id)}>
                  {category.full_path || category.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="format">{t('export.format')}</Label>
          <div className="flex gap-2">
            <Button
              variant={format === 'csv' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFormat('csv')}
              className="flex items-center gap-2"
            >
              <FileText className="h-4 w-4" />
              {t('export.csv')}
            </Button>
            <Button
              variant={format === 'xlsx' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFormat('xlsx')}
              className="flex items-center gap-2"
            >
              <FileSpreadsheet className="h-4 w-4" />
              {t('export.xlsx')}
            </Button>
          </div>
        </div>

        <Button
          onClick={handleExport}
          disabled={isExporting || !startDate || !endDate}
          className="w-full"
        >
          {isExporting ? t('export.button') + '...' : t('export.button')}
        </Button>
      </CardContent>
    </Card>
  )
}
