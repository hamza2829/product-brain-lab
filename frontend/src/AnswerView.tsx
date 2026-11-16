import { ArrowUpRight, FileCheck2, ThumbsDown, ThumbsUp } from 'lucide-react'
import { useState } from 'react'
import { saveFeedback, sourceHref } from './api'
import type { Answer, Citation } from './api'
import { formatDate, SourceBadge } from './SourcePresentation'

const modeLabels: Record<Answer['answer_mode'], string> = {
  extractive: 'Source excerpts',
  'local-model': 'Local model',
  insufficient: 'Limited evidence',
  mock: 'Mock answer',
}

function Feedback({ answerId }: { answerId: string }) {
  const [vote, setVote] = useState<boolean | null>(null)
  const [pending, setPending] = useState(false)
  const [error, setError] = useState(false)

  async function submit(useful: boolean) {
    setPending(true)
    setError(false)
    try {
      await saveFeedback(answerId, useful)
      setVote(useful)
    } catch {
      setError(true)
    } finally {
      setPending(false)
    }
  }

  return (
    <div className="feedback-bar">
      <span id="feedback-label">Was this useful?</span>
      <div className="vote-buttons" role="group" aria-labelledby="feedback-label">
        <button type="button" className="vote" aria-pressed={vote === true} disabled={pending}
          onClick={() => void submit(true)}>
          <ThumbsUp size={15} aria-hidden="true" /> Yes
        </button>
        <button type="button" className="vote" aria-pressed={vote === false} disabled={pending}
          onClick={() => void submit(false)}>
          <ThumbsDown size={15} aria-hidden="true" /> No
        </button>
      </div>
      {error
        ? <span role="alert" className="feedback-error">Feedback couldn’t be saved. Try again.</span>
        : vote !== null && <span role="status" className="feedback-saved">Feedback saved</span>}
    </div>
  )
}

function SourceCard({ citation }: { citation: Citation }) {
  return (
    <a className="source-card" href={sourceHref(citation.id)} target="_blank" rel="noreferrer"
      aria-label={'Open ' + citation.id + ' ' + citation.title + ' in a new tab'}>
      <div className="source-card-top">
        <SourceBadge source={citation.source} />
        <ArrowUpRight size={17} aria-hidden="true" />
      </div>
      <h3>{citation.title}</h3>
      <p>{citation.quote}</p>
      <div className="source-meta">
        <span>{citation.id}</span>
        <time dateTime={citation.date}>{formatDate(citation.date)}</time>
      </div>
    </a>
  )
}

export function AnswerView({ result }: { result: Answer }) {
  const citations = new Map(result.citations.map((citation) => [citation.id, citation]))
  return (
    <>
      <article className="answer-card" aria-labelledby="answer-heading">
        <div className="answer-heading">
          <span className="tile-icon"><FileCheck2 size={21} aria-hidden="true" /></span>
          <h2 id="answer-heading">Answer</h2>
          <span className="mode-label">{modeLabels[result.answer_mode]}</span>
        </div>
        <div className="answer-copy">
          {result.answer.split(/\n\n+/).map((paragraph, index) => (
            <p key={index}>
              {paragraph.split(/(\[[A-Z]+-\d+\])/).map((part, offset) => {
                const id = part.slice(1, -1)
                return part.startsWith('[') && citations.has(id)
                  ? <a className="inline-citation" href={sourceHref(id)} target="_blank"
                      rel="noreferrer" key={offset}>{id}</a>
                  : part
              })}
            </p>
          ))}
        </div>
        <Feedback key={result.answer_id} answerId={result.answer_id} />
      </article>
      {result.citations.length > 0 && (
        <section className="sources-panel" aria-labelledby="citations-heading">
          <h2 id="citations-heading">Cited sources <span>{result.citations.length}</span></h2>
          <div className="source-grid">
            {result.citations.map((citation) => <SourceCard key={citation.id} citation={citation} />)}
          </div>
        </section>
      )}
    </>
  )
}
