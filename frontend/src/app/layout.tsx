import React from 'react'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './css/globals.css'
import { ThemeProvider } from '@/components/theme-provider'
import { AuthProvider } from '@/lib/auth/context'

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: 'MiniUI',
  description: 'Open-source low-code application builder',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang='en' suppressHydrationWarning>
      <head>
        <link rel='icon' href='/favicon.svg' type='image/svg+xml' />
      </head>
      <body className={`${inter.className}`}>
        <ThemeProvider
          attribute='class'
          defaultTheme='system'
          enableSystem
          disableTransitionOnChange>
          <AuthProvider>
            {children}
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
