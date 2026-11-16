import { SlidersHorizontal } from 'lucide-react'
import type { Filters, Source } from './api'
import { SOURCES } from './SourcePresentation'

export const EMPTY_FILTERS: Filters = { sources: [], from_date: '', to_date: '' }

export function FiltersPanel({ value, onChange, changedSinceSearch }: {
  value: Filters
  onChange: (value: Filters) => void
  changedSinceSearch: boolean
}) {
  const hasFilters = Boolean(value.sources.length || value.from_date || value.to_date)

  function toggleSource(source: Source) {
    const sources = value.sources.includes(source)
      ? value.sources.filter((item) => item !== source)
      : [...value.sources, source]
    onChange({ ...value, sources })
  }

  return (
    <aside className="filters-panel" aria-labelledby="filters-title">
      <div className="panel-heading">
        <h2 id="filters-title"><SlidersHorizontal size={17} aria-hidden="true" /> Filters</h2>
        <button
          type="button"
          className="link-button"
          disabled={!hasFilters}
          onClick={() => onChange(EMPTY_FILTERS)}
        >
          Reset
        </button>
      </div>
      <fieldset>
        <legend>Sources</legend>
        <p className="field-hint">{value.sources.length ? 'Search selected sources' : 'Searching all sources'}</p>
        {SOURCES.map(({ id, label, Icon }) => (
          <label className="source-option" key={id}>
            <input
              type="checkbox"
              checked={value.sources.includes(id)}
              onChange={() => toggleSource(id)}
            />
            <Icon size={17} aria-hidden="true" />
            {label}
          </label>
        ))}
      </fieldset>
      <fieldset className="date-filters">
        <legend>Record date</legend>
        <label>
          <span>From</span>
          <input type="date" value={value.from_date} onChange={(event) => (
            onChange({ ...value, from_date: event.target.value })
          )} />
        </label>
        <label>
          <span>Through</span>
          <input type="date" value={value.to_date} onChange={(event) => (
            onChange({ ...value, to_date: event.target.value })
          )} />
        </label>
      </fieldset>
      {changedSinceSearch && <p className="field-hint filters-notice">Search again to apply these filters.</p>}
    </aside>
  )
}
