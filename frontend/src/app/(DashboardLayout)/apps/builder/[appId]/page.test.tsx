import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

const { pushMock, paramsMock } = vi.hoisted(() => ({
  pushMock: vi.fn(),
  paramsMock: vi.fn(),
}))

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: pushMock }),
  useParams: () => paramsMock(),
}))

vi.mock('@iconify/react', () => ({
  Icon: ({ icon }: { icon: string }) => <span data-icon={icon} />,
}))

const { applicationService, pageService, lovService, restDataSourceService } = vi.hoisted(() => ({
  applicationService: {
    getById: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
  },
  pageService: {
    getByAppId: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  },
  lovService: {
    getAll: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  },
  restDataSourceService: {
    getByAppId: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    execute: vi.fn(),
  },
}))

vi.mock('@/app/api/services/applications', () => ({ applicationService }))
vi.mock('@/app/api/services/pages', () => ({ pageService }))
vi.mock('@/app/api/services/lovs', () => ({ lovService }))
vi.mock('@/app/api/services/rest-data-sources', () => ({ restDataSourceService }))

import ApplicationBuilderPage from './page'

const APP = {
  id: 7,
  name: 'HR Portal',
  alias: 'HRAPP',
  description: 'Human resources',
  theme: 'default',
  is_active: true,
}

const PAGE = {
  id: 21,
  application_id: 7,
  name: 'Home',
  alias: 'HOME',
  page_number: 1,
  is_active: true,
}

describe('ApplicationBuilderPage', () => {
  beforeEach(() => {
    pushMock.mockClear()
    paramsMock.mockReset()
    applicationService.getById.mockReset()
    applicationService.create.mockReset()
    applicationService.update.mockReset()
    pageService.getByAppId.mockReset()
    pageService.delete.mockReset()
    lovService.getAll.mockReset()
    restDataSourceService.getByAppId.mockReset()
    vi.stubGlobal('confirm', vi.fn(() => true))
    vi.stubGlobal('alert', vi.fn())
  })

  it('loads an existing application and lists its pages', async () => {
    paramsMock.mockReturnValue({ appId: '7' })
    applicationService.getById.mockResolvedValue(APP)
    pageService.getByAppId.mockResolvedValue([PAGE])
    lovService.getAll.mockResolvedValue([])
    restDataSourceService.getByAppId.mockResolvedValue([])

    render(<ApplicationBuilderPage />)

    expect(await screen.findByText(/application builder: hr portal/i)).toBeInTheDocument()
    expect(applicationService.getById).toHaveBeenCalledWith('7')
    expect(await screen.findByText('Home')).toBeInTheDocument()
    expect(screen.getByText(/application pages \(1\)/i)).toBeInTheDocument()
  })

  it('survives a failing pages lookup but still shows the application', async () => {
    paramsMock.mockReturnValue({ appId: '7' })
    applicationService.getById.mockResolvedValue(APP)
    pageService.getByAppId.mockRejectedValue(new Error('boom'))
    lovService.getAll.mockResolvedValue([])
    restDataSourceService.getByAppId.mockResolvedValue([])

    render(<ApplicationBuilderPage />)

    expect(await screen.findByText(/application builder: hr portal/i)).toBeInTheDocument()
    expect(await screen.findByText(/no pages created yet/i)).toBeInTheDocument()
  })

  it('shows an error when the application cannot be loaded', async () => {
    paramsMock.mockReturnValue({ appId: '7' })
    applicationService.getById.mockRejectedValue(new Error('Application not found'))
    pageService.getByAppId.mockResolvedValue([])
    lovService.getAll.mockResolvedValue([])
    restDataSourceService.getByAppId.mockResolvedValue([])

    render(<ApplicationBuilderPage />)

    expect(await screen.findByText(/application not found/i)).toBeInTheDocument()
  })

  it('creates an application and navigates to its builder', async () => {
    paramsMock.mockReturnValue({ appId: 'new' })
    applicationService.create.mockResolvedValue({ ...APP, id: 99 })
    const user = userEvent.setup()

    render(<ApplicationBuilderPage />)

    expect(await screen.findByText(/create new application/i)).toBeInTheDocument()

    await user.type(screen.getByPlaceholderText(/employee hr portal/i), 'Payroll')
    await user.type(screen.getByPlaceholderText(/hrapp/i), 'PAYROLL')
    await user.click(screen.getByRole('button', { name: /save application/i }))

    await waitFor(() =>
      expect(applicationService.create).toHaveBeenCalledWith(
        expect.objectContaining({ name: 'Payroll', alias: 'PAYROLL' }),
      ),
    )
    expect(pushMock).toHaveBeenCalledWith('/apps/builder/99')
  })

  it('updates an existing application in place', async () => {
    paramsMock.mockReturnValue({ appId: '7' })
    applicationService.getById.mockResolvedValue(APP)
    pageService.getByAppId.mockResolvedValue([PAGE])
    lovService.getAll.mockResolvedValue([])
    restDataSourceService.getByAppId.mockResolvedValue([])
    applicationService.update.mockResolvedValue(APP)
    const user = userEvent.setup()

    render(<ApplicationBuilderPage />)

    const nameInput = await screen.findByDisplayValue('HR Portal')
    await user.clear(nameInput)
    await user.type(nameInput, 'HR Portal v2')
    await user.click(screen.getByRole('button', { name: /save application/i }))

    await waitFor(() =>
      expect(applicationService.update).toHaveBeenCalledWith(
        '7',
        expect.objectContaining({ name: 'HR Portal v2' }),
      ),
    )
    expect(pushMock).not.toHaveBeenCalled()
  })

  it('deletes a page after confirmation and removes it from the list', async () => {
    paramsMock.mockReturnValue({ appId: '7' })
    applicationService.getById.mockResolvedValue(APP)
    pageService.getByAppId.mockResolvedValue([PAGE])
    lovService.getAll.mockResolvedValue([])
    restDataSourceService.getByAppId.mockResolvedValue([])
    pageService.delete.mockResolvedValue(undefined)
    const user = userEvent.setup()

    render(<ApplicationBuilderPage />)

    const deleteButton = await screen.findByTitle(/delete page/i)
    await user.click(deleteButton)

    await waitFor(() => expect(pageService.delete).toHaveBeenCalledWith(21))
    await waitFor(() => expect(screen.queryByText('Home')).not.toBeInTheDocument())
    expect(confirm).toHaveBeenCalled()
  })

  it('does not delete when the user cancels the confirmation', async () => {
    paramsMock.mockReturnValue({ appId: '7' })
    applicationService.getById.mockResolvedValue(APP)
    pageService.getByAppId.mockResolvedValue([PAGE])
    lovService.getAll.mockResolvedValue([])
    restDataSourceService.getByAppId.mockResolvedValue([])
    vi.stubGlobal('confirm', vi.fn(() => false))
    const user = userEvent.setup()

    render(<ApplicationBuilderPage />)

    await user.click(await screen.findByTitle(/delete page/i))

    expect(pageService.delete).not.toHaveBeenCalled()
    expect(screen.getByText('Home')).toBeInTheDocument()
  })
})