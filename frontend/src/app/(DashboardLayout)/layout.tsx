'use client'

import Header from './layout/header/Header'
import Sidebar from './layout/sidebar/Sidebar'
import { AuthGuard } from '@/lib/auth/guard'

export default function Layout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <AuthGuard>
      <div className='flex w-full min-h-screen bg-lightgray dark:bg-dark'>
        <div className='page-wrapper flex w-full'>
          {/* Header/sidebar */}
          <div className='xl:block hidden'>
            <Sidebar />
          </div>

          <div className='body-wrapper w-full'>
            {/* Top Header  */}
            <Header />
            {/* Body Content  */}
            <div className={`container mx-auto px-6 py-6`}>{children}</div>
          </div>
        </div>
      </div>
    </AuthGuard>
  )
}
