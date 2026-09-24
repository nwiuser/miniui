'use client'

import { Icon } from '@iconify/react'

export function PageLoader({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="min-h-[400px] flex items-center justify-center">
      <div className="text-center">
        <Icon
          icon="solar:spinner-linear"
          className="animate-spin text-4xl mx-auto mb-3 text-blue-600"
        />
        <p className="text-sm text-gray-500">{message}</p>
      </div>
    </div>
  )
}

export function InlineLoader() {
  return (
    <div className="flex items-center gap-2 py-2">
      <Icon icon="solar:spinner-linear" className="animate-spin text-lg text-blue-600" />
      <span className="text-xs text-gray-500">Loading...</span>
    </div>
  )
}
