'use client'

import { useState } from 'react'
import { Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Modal } from '@/components/ui/modal'
import { useTranslations } from '@/hooks/useTranslations'
import { CategoryFormModal } from './CategoryFormModal'
import { type Category, type CategorySubmitData } from '@/lib/api'

interface CategoryModalProps {
  onSubmit: (data: CategorySubmitData) => void
  isSubmitting?: boolean
}

export function CategoryModal({ onSubmit, isSubmitting }: CategoryModalProps) {
  const [isOpen, setIsOpen] = useState(false)
  const { t } = useTranslations()

  const handleSubmit = (data: CategorySubmitData) => {
    onSubmit(data)
    setIsOpen(false)
  }

  const handleCancel = () => {
    setIsOpen(false)
  }

  return (
    <>
      <Button
        onClick={() => setIsOpen(true)}
        className="btn-wise w-full"
        size="sm"
      >
        <Plus className="h-4 w-4 mr-2" />
        {t('categories.addButton')}
      </Button>

      <Modal
        isOpen={isOpen}
        onClose={handleCancel}
        title={t('categories.addButton')}
        className="wise-card"
      >
        <CategoryFormModal
          onSubmit={handleSubmit}
          onCancel={handleCancel}
          isSubmitting={isSubmitting}
        />
      </Modal>
    </>
  )
}
