import { test, describe } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dir = dirname(fileURLToPath(import.meta.url));
const root = join(__dir, '..');
const pub = join(root, 'public');

describe('PWA manifest', () => {
  const raw = readFileSync(join(pub, 'manifest.webmanifest'), 'utf8');
  const m = JSON.parse(raw);

  test('has required fields', () => {
    assert.ok(m.name, 'name missing');
    assert.ok(m.short_name, 'short_name missing');
    assert.ok(m.start_url, 'start_url missing');
    assert.equal(m.display, 'standalone');
  });

  test('has id and scope', () => {
    assert.equal(m.id, 'mailprocessor-companion');
    assert.equal(m.scope, '/');
  });

  test('icons list has 192 and 512 entries', () => {
    assert.ok(Array.isArray(m.icons) && m.icons.length >= 2, 'at least 2 icons expected');
    assert.ok(m.icons.some(i => i.sizes === '192x192'), '192x192 icon missing');
    assert.ok(m.icons.some(i => i.sizes === '512x512'), '512x512 icon missing');
  });

  test('theme_color matches brand color', () => {
    assert.equal(m.theme_color, '#1E78C8');
  });
});

describe('PWA service worker', () => {
  const sw = readFileSync(join(pub, 'sw.js'), 'utf8');

  test('sw.js exists in public/', () => {
    assert.ok(existsSync(join(pub, 'sw.js')), 'public/sw.js missing');
  });

  test('sw.js handles install and fetch events', () => {
    assert.ok(sw.includes('install'), 'install event missing');
    assert.ok(sw.includes('fetch'), 'fetch event missing');
    assert.ok(sw.includes('offline'), 'offline URL reference missing');
  });

  test('sw.js activate handler cleans up old caches', () => {
    assert.ok(sw.includes('caches.keys()'), 'activate: caches.keys() missing — old caches not cleaned up');
    assert.ok(sw.includes('caches.delete('), 'activate: caches.delete() missing — old caches not deleted');
  });

  test('sw.js activate handler calls clients.claim()', () => {
    assert.ok(sw.includes('clients.claim()'), 'clients.claim() missing in activate handler');
  });
});

describe('PWA offline fallback', () => {
  test('offline.html exists in public/', () => {
    assert.ok(existsSync(join(pub, 'offline.html')), 'public/offline.html missing');
  });

  test('offline.html is valid HTML with German text', () => {
    const html = readFileSync(join(pub, 'offline.html'), 'utf8');
    assert.ok(html.includes('<!doctype html'), 'doctype missing');
    assert.ok(html.includes('lang="de"'), 'lang=de missing');
    assert.ok(html.includes('Offline') || html.includes('Verbindung'), 'German offline text missing');
  });
});

describe('PWA index.html integration', () => {
  const html = readFileSync(join(root, 'index.html'), 'utf8');

  test('links manifest.webmanifest', () => {
    assert.ok(html.includes('manifest.webmanifest'), 'manifest link missing');
  });

  test('has theme-color meta tag', () => {
    assert.ok(html.includes('theme-color'), 'theme-color meta missing');
  });

  test('registers service worker', () => {
    assert.ok(html.includes('serviceWorker'), 'SW registration missing');
  });

  test('has apple-touch-icon', () => {
    assert.ok(html.includes('apple-touch-icon'), 'apple-touch-icon link missing');
  });
});

describe('PWA icon files', () => {
  test('icon-192.png exists', () => {
    assert.ok(existsSync(join(pub, 'icon-192.png')), 'icon-192.png missing from public/');
  });

  test('icon-512.png exists', () => {
    assert.ok(existsSync(join(pub, 'icon-512.png')), 'icon-512.png missing from public/');
  });

  test('apple-touch-icon.png exists', () => {
    assert.ok(existsSync(join(pub, 'apple-touch-icon.png')), 'apple-touch-icon.png missing from public/');
  });

  test('icon-maskable-192.png exists in public/', () => {
    assert.ok(existsSync(join(pub, 'icon-maskable-192.png')), 'icon-maskable-192.png missing — Android adaptive icons require maskable variant in public/');
  });

  test('icon-maskable-512.png exists in public/', () => {
    assert.ok(existsSync(join(pub, 'icon-maskable-512.png')), 'icon-maskable-512.png missing — Android adaptive icons require maskable variant in public/');
  });
});

describe('PWA manifest maskable icons', () => {
  const raw = readFileSync(join(pub, 'manifest.webmanifest'), 'utf8');
  const m = JSON.parse(raw);

  test('manifest has maskable icon entry', () => {
    assert.ok(m.icons.some(i => i.purpose === 'maskable'), 'no maskable icon in manifest — Android adaptive icons broken');
  });

  test('manifest has maskable-192 entry', () => {
    assert.ok(
      m.icons.some(i => i.purpose === 'maskable' && i.sizes === '192x192'),
      'maskable 192x192 icon missing from manifest'
    );
  });

  test('sw.js ASSETS includes maskable icons', () => {
    const sw = readFileSync(join(pub, 'sw.js'), 'utf8');
    assert.ok(sw.includes('icon-maskable-192.png'), 'sw.js ASSETS missing icon-maskable-192.png');
    assert.ok(sw.includes('icon-maskable-512.png'), 'sw.js ASSETS missing icon-maskable-512.png');
  });
});
