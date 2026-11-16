import {
  ArrowLeft, ArrowRight, BookOpenText, CircleHelp, GitBranch, MessagesSquare, Search, Target,
} from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { ask, getSource, sourceHref } from './api'
import type { Answer, Filters, SourceRecord } from './api'
import { AnswerView } from './AnswerView'
import { EMPTY_FILTERS, FiltersPanel } from './FiltersPanel'
import { formatDate, SourceBadge } from './SourcePresentation'

const examples = [
  {
    kind: 'Decisions',
    question: 'Why did guided setup lead with a teammate invitation instead of CSV import?',
    Icon: GitBranch,
  },
  {
    kind: 'Customer feedback',
    question: 'What did agency coordinators say about sharing with a client who has no login?',
    Icon: MessagesSquare,
  },
  {
    kind: 'Success measures',
    question: 'Which mobile approvals metrics compare speed and reopened requests?',
    Icon: Target,
  },
]

function filterKey(filters: Filters): string {
  return JSON.stringify([[...filters.sources].sort(), filters.from_date, filters.to_date])
}

function QuestionPrompts({ onAsk }: { onAsk: (question: string) => void }) {
  return (
    <section className="prompt-panel" aria-labelledby="prompt-heading">
      <div className="prompt-heading">
        <span className="tile-icon"><CircleHelp size={22} aria-hidden="true" /></span>
        <div>
          <h2 id="prompt-heading">Try a question</h2>
          <p>Start with a topic from the demo workspace.</p>
        </div>
      </div>
      <ul className="prompt-list">
        {examples.map(({ kind, question, Icon }) => (
          <li key={kind}>
            <button type="button" onClick={() => onAsk(question)}>
              <span className="prompt-icon"><Icon size={17} aria-hidden="true" /></span>
              <span><span className="prompt-kind">{kind}</span><span>{question}</span></span>
              <ArrowRight size={17} className="prompt-arrow" aria-hidden="true" />
            </button>
          </li>
        ))}
      </ul>
    </section>
  )
}

function SearchWorkspace() {
  const [question, setQuestion] = useState('')
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS)
  const [appliedFilters, setAppliedFilters] = useState<string | null>(null)
  const [pending, setPending] = useState(false)
  const [result, setResult] = useState<Answer | null>(null)
  const [error, setError] = useState('')
  const search = useRef<AbortController | null>(null)

  useEffect(() => () => search.current?.abort(), [])

  async function runSearch(input: string) {
    const cleanQuestion = input.trim()
    setQuestion(cleanQuestion)
    if (cleanQuestion.length < 3) {
      setError('Enter a question with at least three characters.')
      return
    }
    if (filters.from_date && filters.to_date && filters.from_date > filters.to_date) {
      setError('Choose a start date on or before the end date.')
      return
    }
    search.current?.abort()
    const controller = new AbortController()
    search.current = controller
    setAppliedFilters(filterKey(filters))
    setPending(true)
    setError('')
    setResult(null)
    try {
      const answer = await ask(cleanQuestion, filters, controller.signal)
      if (!controller.signal.aborted) setResult(answer)
    } catch (err) {
      if (!controller.signal.aborted) {
        const message = err instanceof Error ? err.message : 'Check the local API and try again.'
        setError('Search failed. ' + message)
      }
    } finally {
      if (!controller.signal.aborted) setPending(false)
    }
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    void runSearch(question)
  }

  return (
    <main className="workspace" id="main-content">
      <section className="search-area" aria-labelledby="search-heading">
        <h1 id="search-heading">Ask your product <span>workspace.</span></h1>
        <p>Find the decisions, customer feedback, and plans behind your team’s work.</p>
        <form className="search-form" aria-label="Search the workspace" onSubmit={submit}>
          <Search className="search-icon" size={22} aria-hidden="true" />
          <input
            aria-label="Product question"
            type="search"
            value={question}
            required
            minLength={3}
            maxLength={480}
            placeholder="Ask about a product decision, customer insight, or plan…"
            onChange={(event) => setQuestion(event.target.value)}
          />
          <button type="submit" className="search-button" disabled={pending}>
            Search <ArrowRight size={18} aria-hidden="true" />
          </button>
        </form>
      </section>
      <div className="workspace-grid">
        <FiltersPanel value={filters} onChange={setFilters} changedSinceSearch={
          Boolean(result && appliedFilters !== filterKey(filters))
        } />
        <div className="results" aria-live="polite" aria-busy={pending}>
          {error && <p className="error-banner" role="alert">{error}</p>}
          {pending && (
            <div className="pending-panel" role="status">
              <span className="spinner" aria-hidden="true" /> Searching the synthetic workspace…
            </div>
          )}
          {result && <AnswerView result={result} />}
          {!pending && !result && <QuestionPrompts onAsk={(input) => void runSearch(input)} />}
        </div>
      </div>
    </main>
  )
}

function SourceView({ id }: { id: string }) {
  const [record, setRecord] = useState<SourceRecord | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const controller = new AbortController()
    void getSource(id, controller.signal)
      .then((source) => { if (!controller.signal.aborted) setRecord(source) })
      .catch((err: Error) => { if (!controller.signal.aborted) setError(err.message) })
    return () => controller.abort()
  }, [id])

  return (
    <main className="workspace source-view" id="main-content">
      <a className="back-link" href="/"><ArrowLeft size={17} aria-hidden="true" /> Back to search</a>
      {error && <p className="error-banner" role="alert">{error}</p>}
      {!error && !record && <p className="pending-panel" role="status">Loading source…</p>}
      {record && (
        <article className="document-card">
          <div className="document-kicker">
            <SourceBadge source={record.source} /><span>{record.kind}</span><span>{record.id}</span>
          </div>
          <h1>{record.title}</h1>
          <p className="document-byline">
            {record.author} <span aria-hidden="true">·</span>{' '}
            <time dateTime={record.date}>{formatDate(record.date)}</time>
          </p>
          <div className="document-body">{record.body}</div>
          {record.related_ids.length > 0 && (
            <section className="related-records" aria-labelledby="related-label">
              <h2 id="related-label">Related records</h2>
              <ul>
                {record.related_ids.map((related) => (
                  <li key={related}><a href={sourceHref(related)}>{related} <ArrowRight size={14} aria-hidden="true" /></a></li>
                ))}
              </ul>
            </section>
          )}
        </article>
      )}
    </main>
  )
}

export function App() {
  const source = new URLSearchParams(window.location.search).get('source')
  return (
    <>
      <a className="skip-link" href="#main-content">Skip to main content</a>
      <header className="top-bar">
        <div className="top-bar-inner">
          <a href="/" className="brand">
            <span className="brand-mark"><BookOpenText size={22} aria-hidden="true" /></span>
            <span>Product Brain Lab</span>
          </a>
          <div className="workspace-label">
            <span className="workspace-dot" aria-hidden="true" />
            <span>Aster Quay <span className="workspace-tag">· Fictional workspace</span></span>
          </div>
        </div>
      </header>
      {source ? <SourceView key={source} id={source} /> : <SearchWorkspace />}
    </>
  )
}
