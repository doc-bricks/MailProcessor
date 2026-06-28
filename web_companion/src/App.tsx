import { useEffect, useId, useState } from 'react'
import {
  compareTools,
  diffSnapshots,
  getStatusMeta,
  getToolAction,
  parseSnapshotText,
  summarizeSnapshot,
} from './snapshot.js'
import type { MailProcessorSnapshot, MailProcessorToolSnapshot, SnapshotDiff } from './snapshot.js'

const STORAGE_KEY = 'mailprocessor-companion.snapshot.v1'

function formatTimestamp(value: string): string {
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) {
    return value
  }
  return new Intl.DateTimeFormat('de-DE', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(parsed)
}

function statusClass(status: MailProcessorToolSnapshot['status']): string {
  switch (status) {
    case 'available':
      return 'bg-emerald-100 text-emerald-900 ring-1 ring-emerald-200'
    case 'missing':
      return 'bg-rose-100 text-rose-900 ring-1 ring-rose-200'
    case 'not_configured':
      return 'bg-amber-100 text-amber-900 ring-1 ring-amber-200'
    default:
      return 'bg-slate-200 text-slate-800 ring-1 ring-slate-300'
  }
}

function summaryCardClass(kind: 'good' | 'warn' | 'neutral'): string {
  switch (kind) {
    case 'good':
      return 'border-emerald-200 bg-emerald-50'
    case 'warn':
      return 'border-amber-200 bg-amber-50'
    default:
      return 'border-slate-200 bg-white/90'
  }
}

export default function App() {
  const fileInputId = useId()
  const [snapshot, setSnapshot] = useState<MailProcessorSnapshot | null>(null)
  const [importSource, setImportSource] = useState('')
  const [pasteValue, setPasteValue] = useState('')
  const [error, setError] = useState('')
  const [diff, setDiff] = useState<SnapshotDiff | null>(null)

  useEffect(() => {
    const saved = window.localStorage.getItem(STORAGE_KEY)
    if (!saved) {
      return
    }
    try {
      const parsed = parseSnapshotText(saved)
      setSnapshot(parsed)
      setImportSource('Zuletzt lokal gespeicherter Snapshot')
    } catch {
      window.localStorage.removeItem(STORAGE_KEY)
    }
  }, [])

  function applySnapshot(rawText: string, source: string) {
    const parsed = parseSnapshotText(rawText)
    // Diff gegen den aktuell gespeicherten Snapshot berechnen (null = Erstimport)
    setDiff(diffSnapshots(snapshot, parsed))
    setSnapshot(parsed)
    setImportSource(source)
    setError('')
    setPasteValue(rawText)
    window.localStorage.setItem(STORAGE_KEY, rawText)
  }

  async function handleFileImport(file: File | undefined) {
    if (!file) {
      return
    }
    try {
      const text = await file.text()
      applySnapshot(text, file.name)
    } catch (importError) {
      const message = importError instanceof Error ? importError.message : 'Import fehlgeschlagen.'
      setError(message)
    }
  }

  function handlePasteImport() {
    try {
      applySnapshot(pasteValue, 'Manuell eingefügter Snapshot')
    } catch (importError) {
      const message = importError instanceof Error ? importError.message : 'Import fehlgeschlagen.'
      setError(message)
    }
  }

  function clearSnapshot() {
    setSnapshot(null)
    setImportSource('')
    setPasteValue('')
    setError('')
    setDiff(null)
    window.localStorage.removeItem(STORAGE_KEY)
  }

  const summary = snapshot ? summarizeSnapshot(snapshot) : null
  const tools = snapshot ? [...snapshot.tools].sort(compareTools) : []

  return (
    <main className="shell min-h-screen px-4 py-8 text-slate-900 sm:px-6 lg:px-8">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        <section className="overflow-hidden rounded-[2rem] border border-white/70 bg-white/85 shadow-[0_30px_80px_-40px_rgba(15,23,42,0.45)] backdrop-blur">
          <div className="grid gap-0 lg:grid-cols-[minmax(0,1.15fr)_minmax(18rem,0.85fr)]">
            <div className="p-6 sm:p-8">
              <div className="mb-5 flex flex-wrap items-center gap-3">
                <span className="rounded-full bg-sky-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.22em] text-sky-900">
                  Read-only Companion
                </span>
                <span className="rounded-full bg-slate-900 px-3 py-1 text-xs font-semibold text-white">
                  App-ID: com.lukas.mailprocessor
                </span>
              </div>
              <div className="space-y-4">
                <h1 className="max-w-2xl text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">
                  MailProcessor Companion
                </h1>
                <p className="max-w-2xl text-base leading-7 text-slate-700 sm:text-lg">
                  Importiert einen redigierten Desktop-Snapshot und zeigt den Suite-Status lokal,
                  offline und ohne Maildaten oder Zugangsdaten.
                </p>
              </div>

              <div className="mt-8 grid gap-4 lg:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
                <label
                  htmlFor={fileInputId}
                  className="group flex cursor-pointer flex-col justify-between rounded-3xl border border-dashed border-sky-300 bg-sky-50/80 p-5 transition hover:border-sky-500 hover:bg-sky-100/80"
                >
                  <div className="space-y-3">
                    <span className="text-xs font-semibold uppercase tracking-[0.22em] text-sky-800">
                      Datei-Import
                    </span>
                    <p className="text-lg font-semibold text-slate-950">
                      `mailprocessor-suite-v1.json` auswählen
                    </p>
                    <p className="text-sm leading-6 text-slate-700">
                      Ideal für echte Desktop-Exports aus dem Tray-Menü. Der Snapshot wird nur lokal
                      im Browser gespeichert.
                    </p>
                  </div>
                  <div className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-sky-900">
                    Datei wählen
                    <span aria-hidden="true" className="transition group-hover:translate-x-1">
                      →
                    </span>
                  </div>
                  <input
                    id={fileInputId}
                    type="file"
                    accept=".json,application/json"
                    className="sr-only"
                    onChange={async (event) => {
                      await handleFileImport(event.target.files?.[0])
                      event.currentTarget.value = ''
                    }}
                  />
                </label>

                <div className="rounded-3xl border border-slate-200 bg-white/90 p-5">
                  <div className="mb-3 flex items-center justify-between gap-3">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
                        JSON einfügen
                      </p>
                      <p className="mt-1 text-sm text-slate-700">
                        Praktisch für schnelle Zweitgerät- oder PWA-Tests.
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={handlePasteImport}
                      disabled={!pasteValue.trim()}
                      className="rounded-full bg-slate-950 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
                    >
                      Importieren
                    </button>
                  </div>
                  <textarea
                    value={pasteValue}
                    onChange={(event) => {
                      setPasteValue(event.target.value)
                      if (error) {
                        setError('')
                      }
                    }}
                    placeholder='{"schema":"mailprocessor-suite-v1", ... }'
                    className="min-h-40 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 font-mono text-sm leading-6 text-slate-800 outline-none ring-0 transition placeholder:text-slate-400 focus:border-sky-400 focus:bg-white"
                  />
                </div>
              </div>

              <div className="mt-4 flex flex-wrap items-center gap-3 text-sm text-slate-600">
                {importSource ? (
                  <span className="rounded-full bg-slate-100 px-3 py-1.5 font-medium text-slate-700">
                    Quelle: {importSource}
                  </span>
                ) : (
                  <span className="rounded-full bg-slate-100 px-3 py-1.5 font-medium text-slate-700">
                    Noch kein Snapshot importiert
                  </span>
                )}
                {snapshot ? (
                  <button
                    type="button"
                    onClick={clearSnapshot}
                    className="rounded-full border border-slate-300 px-3 py-1.5 font-medium text-slate-700 transition hover:border-slate-500 hover:text-slate-950"
                  >
                    Lokale Referenz löschen
                  </button>
                ) : null}
              </div>

              {error ? (
                <div className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-900">
                  {error}
                </div>
              ) : null}
            </div>

            <aside className="border-t border-slate-200/80 bg-slate-950 px-6 py-6 text-slate-100 lg:border-l lg:border-t-0 sm:px-8">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-sky-300">
                Datenschutzgrenze
              </p>
              <h2 className="mt-3 text-2xl font-semibold">Was diese Ansicht bewusst nicht tut</h2>
              <ul className="mt-5 space-y-3 text-sm leading-6 text-slate-300">
                <li>Keine Mailinhalte, Tokens oder Zugangsdaten speichern.</li>
                <li>Keine Desktop-Prozesse starten oder Fernsteuerung anbieten.</li>
                <li>Keine absoluten Privatpfade akzeptieren oder anzeigen.</li>
                <li>Nur redigierte Tool-Referenzen für spätere Desktop-Wartung halten.</li>
              </ul>

              <div className="mt-8 rounded-3xl border border-white/10 bg-white/5 p-5">
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">
                  Companion-Nutzen
                </p>
                <p className="mt-3 text-sm leading-6 text-slate-200">
                  Unterwegs prüfen, welche Tools installiert sind, welche Version zuletzt erkannt
                  wurde und welche Desktop-Aktion als Nächstes sinnvoll ist.
                </p>
              </div>
            </aside>
          </div>
        </section>

        {diff && (diff.changed.length > 0 || diff.removed.length > 0) ? (
          <section className="rounded-[2rem] border border-amber-200 bg-amber-50 px-6 py-5 shadow-[0_8px_30px_-10px_rgba(15,23,42,0.15)]">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-amber-800">
              Änderungen seit letztem Import
            </p>
            <ul className="mt-3 space-y-2 text-sm text-amber-900">
              {diff.changed.map((entry) => (
                <li key={entry.id} className="flex flex-wrap items-center gap-2">
                  <span className="font-semibold">{entry.display_name}</span>
                  <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium ring-1 ring-amber-200">
                    {entry.from} → {entry.to}
                  </span>
                </li>
              ))}
              {diff.removed.map((id) => (
                <li key={id} className="flex flex-wrap items-center gap-2">
                  <span className="font-semibold">{id}</span>
                  <span className="rounded-full bg-rose-100 px-2 py-0.5 text-xs font-medium text-rose-900 ring-1 ring-rose-200">
                    entfernt
                  </span>
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        {snapshot && summary ? (
          <section className="grid gap-6 lg:grid-cols-[minmax(0,0.78fr)_minmax(19rem,0.22fr)]">
            <div className="space-y-6">
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <article className={`rounded-3xl border p-5 ${summaryCardClass('neutral')}`}>
                  <p className="text-sm font-medium text-slate-500">Tools gesamt</p>
                  <p className="mt-3 text-3xl font-semibold text-slate-950">{summary.total}</p>
                </article>
                <article className={`rounded-3xl border p-5 ${summaryCardClass('good')}`}>
                  <p className="text-sm font-medium text-slate-500">Verfügbar</p>
                  <p className="mt-3 text-3xl font-semibold text-emerald-900">{summary.available}</p>
                </article>
                <article className={`rounded-3xl border p-5 ${summaryCardClass('warn')}`}>
                  <p className="text-sm font-medium text-slate-500">Fehlt oder ungeprüft</p>
                  <p className="mt-3 text-3xl font-semibold text-amber-900">{summary.attention}</p>
                </article>
                <article className={`rounded-3xl border p-5 ${summaryCardClass('neutral')}`}>
                  <p className="text-sm font-medium text-slate-500">Exportiert am</p>
                  <p className="mt-3 text-lg font-semibold text-slate-950">
                    {formatTimestamp(snapshot.exported_at)}
                  </p>
                </article>
              </div>

              <section className="rounded-[2rem] border border-slate-200 bg-white/90 p-6 shadow-[0_30px_70px_-50px_rgba(15,23,42,0.45)]">
                <div className="flex flex-wrap items-end justify-between gap-4">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
                      Snapshot-Übersicht
                    </p>
                    <h2 className="mt-2 text-2xl font-semibold text-slate-950">
                      {snapshot.app.name} {snapshot.app.version || 'ohne Versionsangabe'}
                    </h2>
                    <p className="mt-2 text-sm text-slate-600">
                      Plattform: <span className="font-medium text-slate-800">{snapshot.app.platform}</span>
                    </p>
                  </div>
                  <span className="rounded-full bg-slate-100 px-3 py-1.5 text-sm font-medium text-slate-700">
                    Schema: {snapshot.schema}
                  </span>
                </div>

                <div className="mt-6 grid gap-4 xl:grid-cols-2">
                  {tools.map((tool) => {
                    const meta = getStatusMeta(tool.status)
                    return (
                      <article
                        key={tool.id}
                        className="rounded-3xl border border-slate-200 bg-slate-50/90 p-5"
                      >
                        <div className="flex flex-wrap items-start justify-between gap-3">
                          <div>
                            <h3 className="text-lg font-semibold text-slate-950">
                              {tool.display_name}
                            </h3>
                            <p className="mt-1 text-xs font-medium uppercase tracking-[0.2em] text-slate-500">
                              {tool.id}
                            </p>
                          </div>
                          <span className={`rounded-full px-3 py-1 text-xs font-semibold ${statusClass(tool.status)}`}>
                            {meta.label}
                          </span>
                        </div>

                        <dl className="mt-4 grid gap-3 text-sm text-slate-700 sm:grid-cols-2">
                          <div>
                            <dt className="font-medium text-slate-500">Version</dt>
                            <dd className="mt-1 text-slate-900">{tool.version || 'nicht erkannt'}</dd>
                          </div>
                          <div>
                            <dt className="font-medium text-slate-500">Installiert via</dt>
                            <dd className="mt-1 text-slate-900">{tool.installed_by || 'nicht hinterlegt'}</dd>
                          </div>
                          <div className="sm:col-span-2">
                            <dt className="font-medium text-slate-500">Pfad-Hinweis</dt>
                            <dd className="mt-1 break-all text-slate-900">
                              {tool.path_hint || 'kein Hinweis verfügbar'}
                            </dd>
                          </div>
                        </dl>

                        <div className="mt-4 rounded-2xl bg-white px-4 py-3 text-sm text-slate-700 ring-1 ring-slate-200">
                          <p className="font-medium text-slate-900">Nächste Desktop-Aktion</p>
                          <p className="mt-1">{getToolAction(tool)}</p>
                        </div>
                      </article>
                    )
                  })}
                </div>
              </section>
            </div>

            <aside className="space-y-6">
              <section className="rounded-[2rem] border border-slate-200 bg-white/90 p-6 shadow-[0_30px_70px_-50px_rgba(15,23,42,0.45)]">
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
                  Snapshot-Notizen
                </p>
                <ul className="mt-4 space-y-3 text-sm leading-6 text-slate-700">
                  {snapshot.notes.map((note) => (
                    <li key={note} className="rounded-2xl bg-slate-50 px-4 py-3 ring-1 ring-slate-200">
                      {note}
                    </li>
                  ))}
                </ul>
              </section>

              <section className="rounded-[2rem] border border-slate-200 bg-white/90 p-6 shadow-[0_30px_70px_-50px_rgba(15,23,42,0.45)]">
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
                  Companion-Grenzen
                </p>
                <div className="mt-4 space-y-3 text-sm leading-6 text-slate-700">
                  <p>Diese Ansicht bleibt absichtlich read-only und ersetzt keine lokale MailProcessor-Konfiguration.</p>
                  <p>Android und iOS bleiben PWA-Smokes für denselben Snapshot, keine nativen Voll-Apps.</p>
                </div>
              </section>
            </aside>
          </section>
        ) : (
          <section className="rounded-[2rem] border border-dashed border-slate-300 bg-white/70 px-6 py-10 text-center shadow-[0_30px_70px_-50px_rgba(15,23,42,0.35)]">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
              Import noch offen
            </p>
            <h2 className="mt-3 text-2xl font-semibold text-slate-950">
              Noch kein Desktop-Snapshot geladen
            </h2>
            <p className="mx-auto mt-3 max-w-2xl text-sm leading-7 text-slate-600">
              Lade eine echte `mailprocessor-suite-v1.json` oder füge den JSON-Inhalt direkt ein,
              damit die Companion-Ansicht Toolstatus, Versionen und redigierte Pfad-Hinweise lokal
              darstellen kann.
            </p>
          </section>
        )}
      </div>
    </main>
  )
}
