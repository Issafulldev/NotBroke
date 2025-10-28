'use client'

import { ReactNode } from 'react'

interface LayoutProps {
  sidebar: ReactNode
  main: ReactNode
  summary: ReactNode
  footer?: ReactNode
}

export function Layout({ sidebar, main, summary, footer }: LayoutProps) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Layout desktop - inchangé */}
      <div className="hidden lg:flex h-screen">
        {/* Sidebar pour les catégories */}
        <aside className="w-80 bg-white/60 backdrop-blur-sm border-r border-white/20 shadow-lg overflow-y-auto fade-in">
          <div className="p-6 h-full">
            {sidebar}
          </div>
        </aside>

        {/* Contenu principal */}
        <main className="flex-1 p-8 overflow-y-auto fade-in">
          <div className="max-w-6xl mx-auto">
            {main}
          </div>
        </main>

        {/* Panneau de résumé */}
        <aside className="w-96 bg-white/60 backdrop-blur-sm border-l border-white/20 shadow-lg overflow-y-auto fade-in">
          <div className="p-6 h-full">
            {summary}
          </div>
        </aside>
      </div>

      {/* Layout mobile - flex column */}
      <div className="lg:hidden flex flex-col min-h-screen">
        {/* Contenu principal mobile */}
        <main className="flex-1 p-4">
          {main}
        </main>

        {/* Footer optionnel */}
        {footer && (
          <footer className="bg-white/80 backdrop-blur-sm border-t border-white/20 p-4 fade-in">
            <div className="max-w-6xl mx-auto">
              {footer}
            </div>
          </footer>
        )}
      </div>
    </div>
  )
}
