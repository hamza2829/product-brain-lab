import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import type { Answer, SourceRecord } from './api'
import { App } from './App'

const question = 'Why did guided setup lead with a teammate invitation instead of CSV import?'
const quote = 'Solo trial users abandoned the importer when they lacked a sample file.'

const answer: Answer = {
  answer_id: '7f1a70ae-c269-4e43-9b73-57321702d42a',
  answer_mode: 'extractive',
  answer: quote + ' [CF-001]',
  citations: [{
    id: 'CF-001',
    title: 'Decision record · Guided setup',
    source: 'confluence',
    date: '2025-01-11',
    kind: 'Decision',
    quote,
    score: 0.8,
  }],
  retrieved_source_ids: ['CF-001'],
}

function mockSearch() {
  return vi.fn().mockImplementation(() => Promise.resolve(Response.json(answer)))
}

describe('workspace search', () => {
  it('submits a typed question and renders linked source evidence', async () => {
    const fetch = mockSearch()
    vi.stubGlobal('fetch', fetch)
    render(<App />)
    const user = userEvent.setup()
    await user.type(screen.getByRole('searchbox', { name: 'Product question' }), question + '{Enter}')

    expect(await screen.findByRole('heading', { name: 'Answer' })).toBeVisible()
    const card = screen.getByRole('link', { name: /Open CF-001 Decision record/ })
    expect(card).toHaveAttribute('href', '/?source=CF-001')
    expect(card).toHaveAttribute('target', '_blank')
    expect(card).toHaveTextContent(quote)
    expect(screen.getByRole('link', { name: 'CF-001' })).toHaveAttribute('href', '/?source=CF-001')
    expect(fetch.mock.calls[0][0]).toBe('/api/ask')
    expect(JSON.parse(fetch.mock.calls[0][1].body)).toEqual({
      question, sources: [], from_date: null, to_date: null,
    })
  })

  it('passes source and date filters when asking an example', async () => {
    const fetch = mockSearch()
    vi.stubGlobal('fetch', fetch)
    render(<App />)
    const user = userEvent.setup()
    await user.click(screen.getByRole('checkbox', { name: 'Confluence' }))
    fireEvent.change(screen.getByLabelText('From'), { target: { value: '2025-01-01' } })
    fireEvent.change(screen.getByLabelText('Through'), { target: { value: '2025-01-31' } })
    await user.click(screen.getByRole('button', { name: /Why did guided setup/ }))

    expect(await screen.findByRole('heading', { name: 'Answer' })).toBeVisible()
    expect(JSON.parse(fetch.mock.calls[0][1].body)).toEqual({
      question, sources: ['confluence'], from_date: '2025-01-01', to_date: '2025-01-31',
    })
    await user.click(screen.getByRole('button', { name: 'Reset' }))
    expect(screen.getByRole('checkbox', { name: 'Confluence' })).not.toBeChecked()
    expect(screen.getByLabelText('From')).toHaveValue('')
    expect(screen.getByText('Search again to apply these filters.')).toBeVisible()
  })

  it('shows a reversed-date error without sending a request', async () => {
    const fetch = mockSearch()
    vi.stubGlobal('fetch', fetch)
    render(<App />)
    fireEvent.change(screen.getByLabelText('From'), { target: { value: '2025-02-01' } })
    fireEvent.change(screen.getByLabelText('Through'), { target: { value: '2025-01-01' } })
    await userEvent.click(screen.getByRole('button', { name: /Why did guided setup/ }))
    expect(screen.getByRole('alert')).toHaveTextContent('Choose a start date')
    expect(fetch).not.toHaveBeenCalled()
  })

  it('displays insufficient evidence without a sources section', async () => {
    const fetch = vi.fn().mockResolvedValue(Response.json({
      ...answer,
      citations: [],
      answer_mode: 'insufficient',
      answer: "I couldn't find enough evidence in the selected sources.",
    }))
    vi.stubGlobal('fetch', fetch)
    render(<App />)
    await userEvent.click(screen.getByRole('button', { name: /Why did guided setup/ }))
    expect(await screen.findByText('Limited evidence')).toBeVisible()
    expect(screen.queryByRole('heading', { name: /Cited sources/ })).not.toBeInTheDocument()
  })

  it('surfaces an API failure and lets the user retry', async () => {
    const fetch = mockSearch().mockRejectedValueOnce(new Error('API unavailable'))
    vi.stubGlobal('fetch', fetch)
    render(<App />)
    const user = userEvent.setup()
    await user.click(screen.getByRole('button', { name: /Why did guided setup/ }))
    expect(await screen.findByRole('alert')).toHaveTextContent('API unavailable')
    await user.click(screen.getByRole('button', { name: 'Search' }))
    expect(await screen.findByRole('heading', { name: 'Answer' })).toBeVisible()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
})

describe('answer feedback', () => {
  it('saves and revises a vote against the answer ID', async () => {
    const fetch = mockSearch()
      .mockResolvedValueOnce(Response.json(answer))
      .mockResolvedValueOnce(new Response(null, { status: 204 }))
      .mockResolvedValueOnce(new Response(null, { status: 204 }))
    vi.stubGlobal('fetch', fetch)
    render(<App />)
    const user = userEvent.setup()
    await user.click(screen.getByRole('button', { name: /Why did guided setup/ }))
    await user.click(await screen.findByRole('button', { name: 'Yes' }))
    expect(await screen.findByText('Feedback saved')).toBeVisible()
    expect(screen.getByRole('button', { name: 'Yes' })).toHaveAttribute('aria-pressed', 'true')
    await user.click(screen.getByRole('button', { name: 'No' }))
    await waitFor(() => expect(screen.getByRole('button', { name: 'No' })).toHaveAttribute('aria-pressed', 'true'))
    const voteCalls = fetch.mock.calls.slice(1)
    expect(voteCalls.map(([path]) => path)).toEqual(['/api/feedback', '/api/feedback'])
    expect(voteCalls.map(([, options]) => JSON.parse(options.body))).toEqual([
      { answer_id: answer.answer_id, useful: true },
      { answer_id: answer.answer_id, useful: false },
    ])
  })

  it('keeps a failed vote available to retry', async () => {
    const fetch = mockSearch()
      .mockResolvedValueOnce(Response.json(answer))
      .mockResolvedValueOnce(Response.json({}, { status: 500 }))
    vi.stubGlobal('fetch', fetch)
    render(<App />)
    await userEvent.click(screen.getByRole('button', { name: /Why did guided setup/ }))
    const yes = await screen.findByRole('button', { name: 'Yes' })
    await userEvent.click(yes)
    expect(await screen.findByRole('alert')).toHaveTextContent('Feedback couldn’t be saved')
    expect(yes).toBeEnabled()
    expect(yes).toHaveAttribute('aria-pressed', 'false')
  })
})

describe('source records', () => {
  it('opens the linked full record and lists related records', async () => {
    const doc: SourceRecord = {
      id: 'CF-001', title: 'Decision record · Guided setup', body: quote,
      author: 'Mira Sol', initiative: 'Guided setup', source: 'confluence',
      kind: 'Decision', date: '2025-01-11', related_ids: ['SLACK-001'],
    }
    window.history.replaceState({}, '', '/?source=CF-001')
    const fetch = vi.fn().mockResolvedValue(Response.json(doc))
    vi.stubGlobal('fetch', fetch)
    render(<App />)
    expect(await screen.findByRole('heading', { name: doc.title })).toBeVisible()
    expect(screen.getByText(quote)).toBeVisible()
    expect(screen.getByRole('link', { name: 'SLACK-001' })).toHaveAttribute('href', '/?source=SLACK-001')
    expect(screen.getByRole('link', { name: 'Back to search' })).toHaveAttribute('href', '/')
    expect(fetch.mock.calls[0][0]).toBe('/api/sources/CF-001')
  })

  it('reports a missing record and offers navigation back', async () => {
    window.history.replaceState({}, '', '/?source=CF-404')
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(Response.json(
      { detail: 'Source record not found' }, { status: 404 },
    )))
    render(<App />)
    expect(await screen.findByRole('alert')).toHaveTextContent('Source record not found')
    expect(screen.getByRole('link', { name: 'Back to search' })).toBeVisible()
  })
})
