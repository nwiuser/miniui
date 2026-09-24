'use client'

import FullLogo from '@/app/(DashboardLayout)/layout/shared/logo/FullLogo'
import CardBox from '../shared/CardBox'
import Link from 'next/link'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAuth } from '@/lib/auth/context'
import { useRouter } from 'next/navigation'
import { useState } from 'react'

export const Login = () => {
  const { login, isAuthenticated } = useAuth()
  const router = useRouter()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  if (isAuthenticated) {
    router.push('/')
    return null
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await login(username, password, 1)
      router.push('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <div className='h-screen w-full flex justify-center items-center bg-lightprimary'>
        <div className='md:min-w-[450px] min-w-max'>
          <CardBox>
            <div className='flex justify-center mb-4'>
              <FullLogo />
            </div>
            <p className='text-sm text-charcoal text-center mb-6'>
              Sign in to MiniUI
            </p>
            {error && (
              <div className='mb-4 p-3 rounded bg-red-50 border border-red-200 text-red-700 text-sm'>
                {error}
              </div>
            )}
            <form onSubmit={handleSubmit}>
              <div className='mb-4'>
                <div className='mb-2 block'>
                  <Label htmlFor='username' className='font-medium'>
                    Username
                  </Label>
                </div>
                <Input
                  id='username'
                  type='text'
                  placeholder='Enter your username'
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                />
              </div>
              <div className='mb-4'>
                <div className='mb-2 block'>
                  <Label htmlFor='password' className='font-medium'>
                    Password
                  </Label>
                </div>
                <Input
                  id='password'
                  type='password'
                  placeholder='Enter your password'
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
              <Button
                type='submit'
                className='w-full rounded-full'
                disabled={loading}
              >
                {loading ? 'Signing in...' : 'Sign In'}
              </Button>
            </form>
            <div className='flex items-center gap-2 justify-center mt-6 flex-wrap'>
              <p className='text-base font-medium text-link dark:text-darklink'>
                New to MiniUI?
              </p>
              <Link
                href='/auth/register'
                className='text-sm font-medium text-primary hover:text-primaryemphasis'>
                Create an account
              </Link>
            </div>
          </CardBox>
        </div>
      </div>
    </>
  )
}
