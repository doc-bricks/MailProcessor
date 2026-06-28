import { describe, test } from 'node:test'
import assert from 'node:assert/strict'

import {
  SNAPSHOT_SCHEMA,
  compareTools,
  diffSnapshots,
  getToolAction,
  parseSnapshotText,
  summarizeSnapshot,
} from '../src/snapshot.js'

function buildFixture(overrides = {}) {
  return {
    schema: SNAPSHOT_SCHEMA,
    exported_at: '2026-06-25T09:15:00+02:00',
    app: {
      name: 'MailProcessor',
      version: '0.1.0',
      platform: 'windows',
    },
    tools: [
      {
        id: 'universal_mail_cleaner',
        display_name: 'Universal Mail Cleaner',
        enabled: true,
        installed_by: 'github',
        version: 'v1.2.0',
        status: 'available',
        path_hint: 'LOCALAPPDATA/MailProcessor/tools/universal_mail_cleaner',
      },
      {
        id: 'universal_docs_grabber',
        display_name: 'Universal Docs Grabber',
        enabled: true,
        installed_by: 'manual',
        version: null,
        status: 'missing',
        path_hint: '.../MailTools/UniversalDocsGrabber',
      },
      {
        id: 'universal_invoice_mail',
        display_name: 'Universal Invoice Mail',
        enabled: false,
        installed_by: null,
        version: null,
        status: 'not_configured',
        path_hint: null,
      },
    ],
    notes: [
      'Snapshot enthält keine Maildaten und keine Zugangsdaten.',
      'Pfade sind redigiert und nur als Hinweis für den Desktop-Abgleich gedacht.',
    ],
    ...overrides,
  }
}

describe('snapshot import contract', () => {
  test('parses a valid redacted snapshot', () => {
    const snapshot = parseSnapshotText(JSON.stringify(buildFixture()))

    assert.equal(snapshot.schema, SNAPSHOT_SCHEMA)
    assert.equal(snapshot.app.name, 'MailProcessor')
    assert.equal(snapshot.tools[0].path_hint, 'LOCALAPPDATA/MailProcessor/tools/universal_mail_cleaner')
    assert.equal(snapshot.tools[1].status, 'missing')
    assert.equal(snapshot.notes.length, 2)
  })

  test('rejects wrong schema', () => {
    assert.throws(
      () => parseSnapshotText(JSON.stringify(buildFixture({ schema: 'mailprocessor-suite-v0' }))),
      /Falsches Schema/,
    )
  })

  test('rejects absolute private paths', () => {
    const fixture = buildFixture()
    fixture.tools[0].path_hint = 'C:\\Users\\lukas\\AppData\\Local\\MailProcessor\\tools\\universal_mail_cleaner'

    assert.throws(
      () => parseSnapshotText(JSON.stringify(fixture)),
      /absoluten Privatpfad/,
    )
  })

  test('summarizes tool states for the status cards', () => {
    const summary = summarizeSnapshot(parseSnapshotText(JSON.stringify(buildFixture())))

    assert.deepEqual(summary, {
      total: 3,
      available: 1,
      missing: 1,
      notConfigured: 1,
      unknown: 0,
      attention: 2,
    })
  })

  test('sorts attention items before healthy tools and derives next action text', () => {
    const snapshot = parseSnapshotText(JSON.stringify(buildFixture()))
    const sorted = [...snapshot.tools].sort(compareTools)

    assert.equal(sorted[0].status, 'missing')
    assert.match(getToolAction(sorted[0]), /Pfad oder Installation prüfen/)
    assert.match(getToolAction(sorted[2]), /Kein Eingriff nötig/)
  })
})

// ── diffSnapshots (Schritt 3/4 Portierung — 2026-06-28) ────────────────────
describe('diffSnapshots', () => {
  function parse(overrides = {}) {
    return parseSnapshotText(JSON.stringify(buildFixture(overrides)))
  }

  test('null als vorheriger Snapshot: alle aktuellen Tools sind "added"', () => {
    const curr = parse()
    const diff = diffSnapshots(null, curr)

    assert.deepEqual(diff.changed, [])
    assert.deepEqual(diff.removed, [])
    assert.equal(diff.added.length, curr.tools.length)
    assert.ok(diff.added.includes('universal_mail_cleaner'))
  })

  test('identische Snapshots ergeben leeren Diff', () => {
    const snap = parse()
    const diff = diffSnapshots(snap, snap)

    assert.deepEqual(diff, { changed: [], added: [], removed: [] })
  })

  test('erkennt Statusänderung eines Tools', () => {
    const prev = parse()
    // universal_mail_cleaner war "available", jetzt "missing"
    const currFixture = buildFixture()
    currFixture.tools[0].status = 'missing'
    const curr = parseSnapshotText(JSON.stringify(currFixture))

    const diff = diffSnapshots(prev, curr)

    assert.equal(diff.changed.length, 1)
    assert.equal(diff.changed[0].id, 'universal_mail_cleaner')
    assert.equal(diff.changed[0].from, 'available')
    assert.equal(diff.changed[0].to, 'missing')
    assert.deepEqual(diff.added, [])
    assert.deepEqual(diff.removed, [])
  })

  test('erkennt neu hinzugefügtes Tool', () => {
    const prev = parse()
    const currFixture = buildFixture()
    currFixture.tools.push({
      id: 'universal_attachment_store',
      display_name: 'Universal Attachment Store',
      enabled: true,
      installed_by: 'github',
      version: 'v0.5.0',
      status: 'available',
      path_hint: 'LOCALAPPDATA/MailProcessor/tools/universal_attachment_store',
    })
    const curr = parseSnapshotText(JSON.stringify(currFixture))

    const diff = diffSnapshots(prev, curr)

    assert.ok(diff.added.includes('universal_attachment_store'), 'neues Tool muss in added stehen')
    assert.deepEqual(diff.changed, [])
    assert.deepEqual(diff.removed, [])
  })

  test('erkennt entferntes Tool', () => {
    const prevFixture = buildFixture()
    prevFixture.tools.push({
      id: 'legacy_tool',
      display_name: 'Legacy Tool',
      enabled: false,
      installed_by: null,
      version: null,
      status: 'not_configured',
      path_hint: null,
    })
    const prev = parseSnapshotText(JSON.stringify(prevFixture))
    const curr = parse()

    const diff = diffSnapshots(prev, curr)

    assert.ok(diff.removed.includes('legacy_tool'), 'entferntes Tool muss in removed stehen')
    assert.deepEqual(diff.changed, [])
    assert.deepEqual(diff.added, [])
  })
})
