export type ToolStatus = 'available' | 'missing' | 'not_configured' | 'unknown'

export interface MailProcessorToolSnapshot {
  id: string
  display_name: string
  enabled: boolean
  installed_by: string | null
  version: string | null
  status: ToolStatus
  path_hint: string | null
}

export interface MailProcessorSnapshot {
  schema: string
  exported_at: string
  app: {
    name: string
    version: string
    platform: string
  }
  tools: MailProcessorToolSnapshot[]
  notes: string[]
}

export interface SnapshotSummary {
  total: number
  available: number
  missing: number
  notConfigured: number
  unknown: number
  attention: number
}

export declare const SNAPSHOT_SCHEMA: 'mailprocessor-suite-v1'

export declare function parseSnapshotText(rawText: string): MailProcessorSnapshot
export declare function summarizeSnapshot(snapshot: MailProcessorSnapshot): SnapshotSummary
export declare function compareTools(
  left: MailProcessorToolSnapshot,
  right: MailProcessorToolSnapshot,
): number
export declare function getStatusMeta(status: ToolStatus): { label: string }
export declare function getToolAction(tool: MailProcessorToolSnapshot): string

export interface SnapshotDiffEntry {
  id: string
  display_name: string
  from: ToolStatus
  to: ToolStatus
}

export interface SnapshotDiff {
  changed: SnapshotDiffEntry[]
  added: string[]
  removed: string[]
}

export declare function diffSnapshots(
  prev: MailProcessorSnapshot | null,
  curr: MailProcessorSnapshot,
): SnapshotDiff
