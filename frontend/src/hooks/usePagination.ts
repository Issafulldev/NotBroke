import { useState, useCallback } from 'react'

export interface PaginationState {
  page: number
  perPage: number
}

export function usePagination(initialPage = 1, initialPerPage = 20) {
  const [page, setPage] = useState(initialPage)
  const [perPage, setPerPage] = useState(initialPerPage)

  const nextPage = useCallback(() => {
    setPage((prev) => prev + 1)
  }, [])

  const previousPage = useCallback(() => {
    setPage((prev) => Math.max(1, prev - 1))
  }, [])

  const setPagination = useCallback((newPage: number, newPerPage: number) => {
    setPage(newPage)
    setPerPage(newPerPage)
  }, [])

  return {
    page,
    perPage,
    setPage,
    setPerPage,
    nextPage,
    previousPage,
    setPagination,
  }
}
