import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

const { pushMock } = vi.hoisted(() => ({ pushMock: vi.fn() }))
const { useAuthMock } = vi.hoisted(() => ({ useAuthMock: vi.fn() }))

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: pushMock }),
}))

vi.mock('@/lib/auth/context', () => ({
  useAuth: () => useAuthMock(),
}))

import { Login } from './login'

function auth(overrides: Partial<ReturnType<typeof useAuthMock>> = {}) {
  useAuthMock.mockReturnValue({
    login: vi.fn().mockResolvedValue(undefined),
    isAuthenticated: false,
    isLoading: false,
    user: null,
    token: null,
    logout: vi.fn(),
    ...overrides,
  })
}

describe('Login', () => {
  beforeEach(() => {
    pushMock.mockClear()
    useAuthMock.mockReset()
  })

  it('renders the username and password fields and the submit button', () => {
    auth()
    render(<Login />)

    expect(screen.getByLabelText(/username/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
    expect(screen.getByText(/sign in to miniui/i)).toBeInTheDocument()
  })

  it('calls login with the entered credentials and application 1, then redirects', async () => {
    const login = vi.fn().mockResolvedValue(undefined)
    auth({ login })
    const user = userEvent.setup()
    render(<Login />)

    await user.type(screen.getByLabelText(/username/i), 'ada')
    await user.type(screen.getByLabelText(/password/i), 'StrongPass1!')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => expect(login).toHaveBeenCalledWith('ada', 'StrongPass1!', 1))
    expect(pushMock).toHaveBeenCalledWith('/')
  })

  it('shows the error returned by login and stays on the form', async () => {
    const login = vi.fn().mockRejectedValue(new Error('Incorrect username or password'))
    auth({ login })
    const user = userEvent.setup()
    render(<Login />)

    await user.type(screen.getByLabelText(/username/i), 'ada')
    await user.type(screen.getByLabelText(/password/i), 'wrong')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    expect(await screen.findByText('Incorrect username or password')).toBeInTheDocument()
    expect(pushMock).not.toHaveBeenCalled()
  })

  it('disables the button and labels it while the request is in flight', async () => {
    let resolveLogin: () => void = () => {}
    const login = vi.fn(
      () =>
        new Promise<void>((resolve) => {
          resolveLogin = resolve
        }),
    )
    auth({ login })
    const user = userEvent.setup()
    render(<Login />)

    await user.type(screen.getByLabelText(/username/i), 'ada')
    await user.type(screen.getByLabelText(/password/i), 'StrongPass1!')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    const pending = screen.getByRole('button', { name: /signing in/i })
    expect(pending).toBeDisabled()

    resolveLogin()
    await waitFor(() => expect(pushMock).toHaveBeenCalledWith('/'))
  })

  it('shows a generic message for a non-Error rejection', async () => {
    auth({ login: vi.fn().mockRejectedValue('boom') })
    const user = userEvent.setup()
    render(<Login />)

    await user.type(screen.getByLabelText(/username/i), 'ada')
    await user.type(screen.getByLabelText(/password/i), 'x')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    expect(await screen.findByText('Login failed')).toBeInTheDocument()
  })

  it('redirects immediately when already authenticated and renders no form', () => {
    auth({ isAuthenticated: true })
    const { container } = render(<Login />)

    expect(pushMock).toHaveBeenCalledWith('/')
    expect(container).toBeEmptyDOMElement()
  })

  it('links to the registration page', () => {
    auth()
    render(<Login />)

    expect(screen.getByRole('link', { name: /create an account/i })).toHaveAttribute(
      'href',
      '/auth/register',
    )
  })
})
