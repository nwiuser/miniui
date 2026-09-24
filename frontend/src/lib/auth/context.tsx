'use client'

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'

interface User {
  user_id: number
  username: string
  email: string
  first_name: string
  last_name: string
  administrator_role: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  isLoading: boolean
  login: (username: string, password: string, applicationId: number) => Promise<void>
  logout: () => Promise<void>
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const TOKEN_KEY = 'miniui_token'
const USER_KEY = 'miniui_user'

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const storedToken = localStorage.getItem(TOKEN_KEY)
    const storedUser = localStorage.getItem(USER_KEY)
    if (storedToken && storedUser) {
      setToken(storedToken)
      setUser(JSON.parse(storedUser))
    }
    setIsLoading(false)
  }, [])

  const login = useCallback(async (username: string, password: string, applicationId: number) => {
    const formData = new URLSearchParams()
    formData.append('username', username)
    formData.append('password', password)
    formData.append('application_id', applicationId.toString())

    const response = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Requested-With': 'XMLHttpRequest',
      },
      body: formData.toString(),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => null)
      throw new Error(errorData?.detail || 'Login failed')
    }

    const data = await response.json()

    const userData: User = {
      user_id: data.user_id,
      username: data.username,
      email: data.email,
      first_name: data.first_name,
      last_name: data.last_name,
      administrator_role: data.administrator_role,
    }

    localStorage.setItem(TOKEN_KEY, data.access_token)
    localStorage.setItem(USER_KEY, JSON.stringify(userData))
    setToken(data.access_token)
    setUser(userData)
  }, [])

  const logout = useCallback(async () => {
    if (token) {
      try {
        const formData = new URLSearchParams()
        formData.append('session_id', token)

        await fetch('/api/v1/auth/logout', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest',
          },
          body: formData.toString(),
        })
      } catch {
        // Logout even if API call fails
      }
    }

    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    setToken(null)
    setUser(null)
  }, [token])

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        login,
        logout,
        isAuthenticated: !!token,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
