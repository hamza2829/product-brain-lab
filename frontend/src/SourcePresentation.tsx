import { BookOpen, FolderOpen, MessagesSquare, SquareKanban } from 'lucide-react'
import type { Source } from './api'

export const SOURCES = [
  { id: 'jira', label: 'Jira', Icon: SquareKanban },
  { id: 'confluence', label: 'Confluence', Icon: BookOpen },
  { id: 'slack', label: 'Slack', Icon: MessagesSquare },
  { id: 'sharepoint', label: 'SharePoint', Icon: FolderOpen },
] as const

export function SourceBadge({ source }: { source: Source }) {
  const { label, Icon } = SOURCES.find(({ id }) => id === source)!
  return (
    <span className={'source-badge source-' + source}>
      <Icon size={15} aria-hidden="true" />
      {label}
    </span>
  )
}

export function formatDate(value: string): string {
  return new Intl.DateTimeFormat('en', {
    dateStyle: 'medium',
    timeZone: 'UTC',
  }).format(new Date(value))
}
