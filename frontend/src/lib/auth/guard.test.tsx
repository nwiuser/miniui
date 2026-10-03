import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'

const { pushMock } = vi.hoisted(() => ({ pushMock: vi.fn() }))
const { useAuthMock } = vi.hoisted(() => ({ useAuthMock: vi.fn() }))

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: pushMock }),
}))

vi.mock('@/lib/auth/context', () => ({
  useAuth: () => useAuthMock(),
}))

import { AuthGuard } from './guard'

function auth(overrides: Record<string, unknown> = {}) {
  useAuthMock.mockReturnValue({
    isAuthenticated: false,
    isLoading: false,
    user: null,
    token: null,
    login: vi.fn(),
    logout: vi.fn(),
    ...overrides,
  })
}

describe('AuthGuard', () => {
  beforeEach(() => {
    pushMock.mockClear()
    useAuthMock.mockReset()
  })

  it('redirects to the login page when the user is not authenticated', async () => {
    auth({ isAuthenticated: false, isLoading: false })
    render(
      <AuthGuard>
        <p>secret</p>
      </AuthGuard>,
    )

    await waitFor(() => expect(pushMock).toHaveBeenCalledWith('/auth/login'))
    expect(screen.queryByText('secret')).not.toBeInTheDocument()
  })

  it('shows a loading state while the stored session is being read', () => {
    auth({ isAuthenticated: false, isLoading: true })
    render(
      <AuthGuard>
        <p>secret</p>
      </AuthGuard>,
    )

    expect(screen.getByText(/loading/i)).toBeInTheDocument()
    expect(pushMock).not.toHaveBeenCalled()
  })

  it('renders the children once authenticated', () => {
    auth({ isAuthenticated: true, isLoading: false })
    render(
      <AuthGuard>
        <p>secret</p>
      </AuthGuard>,
    )

    expect(screen.getByText('secret')).toBeInTheDocument()
    expect(pushMock).not.toHaveBeenCalled()
  })
})