export const SNAPSHOT_SCHEMA = 'mailprocessor-suite-v1'

const VALID_STATUSES = new Set(['available', 'missing', 'not_configured', 'unknown'])
const STATUS_ORDER = {
  missing: 0,
  not_configured: 1,
  unknown: 2,
  available: 3,
}
const PRIVATE_PATH_PATTERNS = [
  /^[A-Za-z]:[\\/]/,
  /^\\\\/,
  /^\/Users\//i,
  /^\/home\//i,
]

function asRecord(value) {
  return typeof value === 'object' && value !== null && !Array.isArray(value) ? value : null
}

function assertString(value, message) {
  if (typeof value !== 'string' || !value.trim()) {
    throw new Error(message)
  }
  return value
}

function assertBoolean(value, message) {
  if (typeof value !== 'boolean') {
    throw new Error(message)
  }
  return value
}

function assertSafePathHint(value) {
  if (value == null) {
    return null
  }
  const text = assertString(value, 'Path-Hinweis muss ein String sein.')
  if (PRIVATE_PATH_PATTERNS.some((pattern) => pattern.test(text))) {
    throw new Error('Snapshot enthält einen absoluten Privatpfad und wurde abgelehnt.')
  }
  return text
}

export function parseSnapshotText(rawText) {
  const sourceText = assertString(rawText, 'Snapshot-Inhalt fehlt.')

  let parsed
  try {
    parsed = JSON.parse(sourceText)
  } catch {
    throw new Error('Snapshot ist kein gültiges JSON.')
  }

  const snapshot = asRecord(parsed)
  if (!snapshot) {
    throw new Error('Snapshot muss ein JSON-Objekt sein.')
  }
  if (snapshot.schema !== SNAPSHOT_SCHEMA) {
    throw new Error(`Falsches Schema: erwartet ${SNAPSHOT_SCHEMA}.`)
  }

  const app = asRecord(snapshot.app)
  if (!app) {
    throw new Error('Snapshot.app fehlt oder ist ungültig.')
  }

  if (!Array.isArray(snapshot.tools)) {
    throw new Error('Snapshot.tools muss eine Liste sein.')
  }

  const notes = Array.isArray(snapshot.notes)
    ? snapshot.notes.map((note) => assertString(note, 'Snapshot-Notiz muss Text sein.'))
    : []

  return {
    schema: SNAPSHOT_SCHEMA,
    exported_at: assertString(snapshot.exported_at, 'Snapshot.exported_at fehlt.'),
    app: {
      name: assertString(app.name, 'Snapshot.app.name fehlt.'),
      version: typeof app.version === 'string' ? app.version : '',
      platform: assertString(app.platform, 'Snapshot.app.platform fehlt.'),
    },
    tools: snapshot.tools.map((tool, index) => normalizeTool(tool, index)),
    notes,
  }
}

function normalizeTool(value, index) {
  const tool = asRecord(value)
  if (!tool) {
    throw new Error(`Tool-Eintrag ${index + 1} ist ungültig.`)
  }

  const status = assertString(tool.status, `Tool ${index + 1}: status fehlt.`)
  if (!VALID_STATUSES.has(status)) {
    throw new Error(`Tool ${index + 1}: unbekannter Status "${status}".`)
  }

  return {
    id: assertString(tool.id, `Tool ${index + 1}: id fehlt.`),
    display_name: assertString(tool.display_name, `Tool ${index + 1}: display_name fehlt.`),
    enabled: assertBoolean(tool.enabled, `Tool ${index + 1}: enabled fehlt.`),
    installed_by: typeof tool.installed_by === 'string' ? tool.installed_by : null,
    version: typeof tool.version === 'string' ? tool.version : null,
    status,
    path_hint: assertSafePathHint(tool.path_hint),
  }
}

export function summarizeSnapshot(snapshot) {
  const tools = snapshot.tools || []
  const available = tools.filter((tool) => tool.status === 'available').length
  const missing = tools.filter((tool) => tool.status === 'missing').length
  const notConfigured = tools.filter((tool) => tool.status === 'not_configured').length
  const unknown = tools.filter((tool) => tool.status === 'unknown').length

  return {
    total: tools.length,
    available,
    missing,
    notConfigured,
    unknown,
    attention: missing + notConfigured + unknown,
  }
}

export function compareTools(left, right) {
  const leftRank = STATUS_ORDER[left.status] ?? 99
  const rightRank = STATUS_ORDER[right.status] ?? 99
  if (leftRank !== rightRank) {
    return leftRank - rightRank
  }
  return left.display_name.localeCompare(right.display_name, 'de')
}

export function getStatusMeta(status) {
  switch (status) {
    case 'available':
      return { label: 'Verfügbar' }
    case 'missing':
      return { label: 'Fehlt' }
    case 'not_configured':
      return { label: 'Nicht eingerichtet' }
    default:
      return { label: 'Unbekannt' }
  }
}

export function getToolAction(tool) {
  switch (tool.status) {
    case 'available':
      return 'Kein Eingriff nötig. Bei Bedarf Version und Pfad-Hinweis am Desktop gegenprüfen.'
    case 'missing':
      return 'Am Desktop Pfad oder Installation prüfen und danach erneut exportieren.'
    case 'not_configured':
      return 'Tool im Desktop-Assistenten einrichten oder per GitHub-Installer ergänzen.'
    default:
      return 'Status am Desktop neu scannen, damit der Snapshot wieder eindeutig wird.'
  }
}

/**
 * Vergleicht zwei Snapshots und gibt zurück, welche Tools sich geändert,
 * neu hinzugekommen oder entfernt wurden.
 *
 * @param {import('./snapshot.js').MailProcessorSnapshot | null} prev  — vorheriger Snapshot oder null
 * @param {import('./snapshot.js').MailProcessorSnapshot}        curr  — neuer Snapshot
 * @returns {{ changed: Array<{id: string, display_name: string, from: string, to: string}>, added: string[], removed: string[] }}
 */
export function diffSnapshots(prev, curr) {
  if (!prev) {
    return {
      changed: [],
      added: curr.tools.map((t) => t.id),
      removed: [],
    }
  }

  const prevById = new Map(prev.tools.map((t) => [t.id, t]))
  const currById = new Map(curr.tools.map((t) => [t.id, t]))

  const changed = []
  const added = []
  const removed = []

  for (const [id, tool] of currById) {
    const prevTool = prevById.get(id)
    if (!prevTool) {
      added.push(id)
    } else if (prevTool.status !== tool.status) {
      changed.push({ id, display_name: tool.display_name, from: prevTool.status, to: tool.status })
    }
  }

  for (const id of prevById.keys()) {
    if (!currById.has(id)) {
      removed.push(id)
    }
  }

  return { changed, added, removed }
}
