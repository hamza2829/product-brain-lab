export type Source = 'jira' | 'confluence' | 'slack' | 'sharepoint'

export type Filters = {
  sources: Source[]
  from_date: string
  to_date: string
}

export type Citation = {
  id: string
  title: string
  source: Source
  date: string
  kind: string
  quote: string
  score: number
}

export type Answer = {
  answer_id: string
  answer: string
  answer_mode: 'extractive' | 'local-model' | 'insufficient' | 'mock'
  citations: Citation[]
  retrieved_source_ids: string[]
}

export type SourceRecord = Pick<Citation, 'id' | 'title' | 'source' | 'date' | 'kind'> & {
  initiative: string
  author: string
  body: string
  related_ids: string[]
}

async function request(path: string, options?: RequestInit): Promise<Response> {
  const response = await fetch(path, options)
  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    const message = typeof error.detail === 'string'
      ? error.detail
      : 'Request failed (' + response.status + ').'
    throw new Error(message)
  }
  return response
}

function post(body: object, signal?: AbortSignal): RequestInit {
  return {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal,
  }
}

export async function ask(question: string, filters: Filters, signal: AbortSignal): Promise<Answer> {
  const response = await request('/api/ask', post({
    question,
    sources: filters.sources,
    from_date: filters.from_date || null,
    to_date: filters.to_date || null,
  }, signal))
  return response.json()
}

export async function getSource(id: string, signal: AbortSignal): Promise<SourceRecord> {
  const response = await request('/api/sources/' + encodeURIComponent(id), { signal })
  return response.json()
}

export async function saveFeedback(answerId: string, useful: boolean): Promise<void> {
  await request('/api/feedback', post({ answer_id: answerId, useful }))
}

export function sourceHref(id: string): string {
  return '/?source=' + encodeURIComponent(id)
}
