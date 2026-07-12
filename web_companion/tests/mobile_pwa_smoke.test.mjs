import { describe, test } from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  SNAPSHOT_SCHEMA,
  diffSnapshots,
  getToolAction,
  parseSnapshotText,
  summarizeSnapshot,
} from '../src/snapshot.js';

const __dir = dirname(fileURLToPath(import.meta.url));
const root = join(__dir, '..');
const pub = join(root, 'public');
const snapshotFixturePath = join(__dir, 'mobile_smoke_snapshot.json');

const privatePathPatterns = [
  /^[A-Za-z]:[\\/]/,
  /^\\\\/,
  /^\/Users\//i,
  /^\/home\//i,
];

const mobileProfiles = [
  {
    name: 'Android Chrome PWA',
    userAgent: 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/126 Mobile Safari/537.36',
    viewport: { width: 393, height: 873 },
    requiredAsset: 'icon-maskable-512.png',
  },
  {
    name: 'iOS Safari PWA',
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 Version/17.5 Mobile/15E148 Safari/604.1',
    viewport: { width: 390, height: 844 },
    requiredAsset: 'apple-touch-icon-180.png',
  },
];

function readJson(path) {
  return JSON.parse(readFileSync(path, 'utf8'));
}

function loadFixture() {
  return parseSnapshotText(readFileSync(snapshotFixturePath, 'utf8'));
}

describe('Android/iOS PWA smoke with real snapshot fixture', () => {
  test('fixture parses as a redacted desktop export', () => {
    const snapshot = loadFixture();

    assert.equal(snapshot.schema, SNAPSHOT_SCHEMA);
    assert.equal(snapshot.app.name, 'MailProcessor');
    assert.equal(snapshot.app.platform, 'windows');
    assert.equal(snapshot.tools.length, 3);
    assert.ok(snapshot.notes.some((note) => note.includes('keine Zugangsdaten')));
  });

  test('status summary exposes the mobile read-only maintenance signal', () => {
    const summary = summarizeSnapshot(loadFixture());

    assert.deepEqual(summary, {
      total: 3,
      available: 1,
      missing: 1,
      notConfigured: 1,
      unknown: 0,
      attention: 2,
    });
  });

  test('path hints stay redacted before local mobile storage', () => {
    const snapshot = loadFixture();

    for (const tool of snapshot.tools) {
      if (!tool.path_hint) {
        continue;
      }
      assert.ok(
        !privatePathPatterns.some((pattern) => pattern.test(tool.path_hint)),
        `${tool.id} exposes a private absolute path`,
      );
    }
  });

  test('mobile re-import detects status drift without server sync', () => {
    const previous = loadFixture();
    const nextPayload = readJson(snapshotFixturePath);
    nextPayload.exported_at = '2026-07-13T00:30:00+02:00';
    nextPayload.tools[1].status = 'available';
    nextPayload.tools[1].path_hint = 'LOCALAPPDATA/MailProcessor/tools/universal_docs_grabber';

    const next = parseSnapshotText(JSON.stringify(nextPayload));
    const diff = diffSnapshots(previous, next);

    assert.equal(diff.changed.length, 1);
    assert.equal(diff.changed[0].id, 'universal_docs_grabber');
    assert.equal(diff.changed[0].from, 'missing');
    assert.equal(diff.changed[0].to, 'available');
    assert.deepEqual(diff.added, []);
    assert.deepEqual(diff.removed, []);
  });

  test('tool actions remain desktop-only and read-only for mobile users', () => {
    const snapshot = loadFixture();
    const missingTool = snapshot.tools.find((tool) => tool.status === 'missing');
    const configuredTool = snapshot.tools.find((tool) => tool.status === 'available');

    assert.match(getToolAction(missingTool), /Desktop/);
    assert.match(getToolAction(missingTool), /erneut exportieren/);
    assert.match(getToolAction(configuredTool), /Kein Eingriff nötig/);
  });
});

describe('Android and iOS PWA shell contract', () => {
  const indexHtml = readFileSync(join(root, 'index.html'), 'utf8');
  const appSource = readFileSync(join(root, 'src', 'App.tsx'), 'utf8');
  const manifest = readJson(join(pub, 'manifest.webmanifest'));
  const serviceWorker = readFileSync(join(pub, 'sw.js'), 'utf8');
  const capacitorConfig = readFileSync(join(root, 'capacitor.config.ts'), 'utf8');

  for (const profile of mobileProfiles) {
    test(`${profile.name} profile is covered by install/offline assets`, () => {
      assert.ok(profile.userAgent.includes('Mobile'), 'mobile user agent marker missing');
      assert.ok(profile.viewport.width <= 430, 'viewport should model a phone-width smoke');
      assert.equal(manifest.display, 'standalone');
      assert.equal(manifest.start_url, '/');
      assert.equal(manifest.scope, '/');
      assert.ok(existsSync(join(pub, profile.requiredAsset)), `${profile.requiredAsset} missing`);
      assert.ok(serviceWorker.includes(profile.requiredAsset), `${profile.requiredAsset} not cached`);
    });
  }

  test('iOS Safari install metadata and safe area are present', () => {
    assert.ok(indexHtml.includes('viewport-fit=cover'), 'viewport-fit=cover missing');
    assert.ok(indexHtml.includes('apple-mobile-web-app-title'), 'iOS app title missing');
    assert.ok(indexHtml.includes('apple-mobile-web-app-status-bar-style'), 'iOS status bar style missing');
    assert.ok(indexHtml.includes('apple-touch-icon-180.png'), 'iOS touch icon missing');
  });

  test('Android shell keeps stable PWA and Capacitor identity', () => {
    assert.equal(manifest.id, 'mailprocessor-companion');
    assert.ok(manifest.icons.some((icon) => icon.purpose === 'maskable'), 'maskable Android icon missing');
    assert.ok(capacitorConfig.includes("appId: 'com.lukas.mailprocessor'"), 'Capacitor appId changed');
  });

  test('companion persists only a local browser reference', () => {
    assert.ok(appSource.includes('mailprocessor-companion.snapshot.v1'), 'snapshot storage key missing');
    assert.ok(appSource.includes('window.localStorage.setItem'), 'localStorage persistence missing');
    assert.ok(!appSource.includes('fetch('), 'companion must not upload snapshots');
    assert.ok(!appSource.includes('WebSocket'), 'mobile smoke should remain read-only');
  });
});
