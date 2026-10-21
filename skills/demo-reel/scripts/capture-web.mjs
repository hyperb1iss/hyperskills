#!/usr/bin/env node
// Deterministic capture of a web page: every frame is a pure function of film
// time, so two runs of the same page give the same frames.
//
// Playwright's page.clock fakes Date, timers, performance and
// requestAnimationFrame, but CSS and Web Animations run on the compositor's
// real clock. An init script seeds Math.random and, after each clock step,
// pauses every animation the first time it appears and pins its currentTime
// to film time. Screenshots are taken at device scale (2 by default, so a
// 1920x1080 viewport gives 3840x2160) and piped straight into ffmpeg.
//
// Needs Node 18+, ffmpeg, and Playwright (resolved from the current
// directory, or DEMO_REEL_PLAYWRIGHT) with its Chromium installed.

import { spawn } from 'node:child_process'
import { createHash } from 'node:crypto'
import { once } from 'node:events'
import fs from 'node:fs'
import { createRequire } from 'node:module'
import path from 'node:path'
import { pathToFileURL } from 'node:url'

const HELP = `Usage: capture-web.mjs --url URL (--out FILE.mp4 | --frames DIR | --still FILE.png) [options]

Source and output:
  --url URL            http(s) URL, file:// URL, or a local file path
  --out FILE.mp4       encode H.264 (yuv420p, bt709 tags) through ffmpeg
  --frames DIR         write numbered PNG frames instead (keeps transparency)
  --still FILE.png     write one frame, at --at milliseconds of film time
  --at MS              film time for --still (default 0)
Timing:
  --seconds S          length of the take (default 5)
  --fps N              frames per second (default 60)
  --warmup MS          advance film time before frame 0 (default 0)
  --time ISO           wall-clock start of the faked clock
                       (default 2026-01-01T12:00:00Z)
  --seed N             Math.random seed (default 1)
Page:
  --width PX --height PX   CSS viewport (default 1920x1080)
  --scale N            device scale factor (default 2, giving 3840x2160)
  --color-scheme light|dark   (default light)
  --transparent        transparent page background (--frames or --still only)
  --eval JS            run JS in the page after warmup (repeatable)
  --press KEY          press a key after warmup, e.g. Space (repeatable)
  --timeout MS         page load timeout (default 60000)
  --browser-arg ARG    extra Chromium switch, e.g. --use-gl=angle (repeatable)
Encoding:
  --crf N              x264 quality (default 16)
  --preset NAME        x264 preset (default medium)
Other:
  --json               print a JSON summary on stdout
  --probe              report whether Playwright resolves and Chromium launches
  -h, --help           show this help

Not driven by film time: <video> and <audio> playback, CSS or JS inside
cross-origin iframes, and work scheduled inside Web Workers. Inside the page,
performance.now() is film time in ms (0 at frame 0 when there is no warmup;
the page loads one frame earlier) and requestAnimationFrame fires once per
captured frame. Date.now() is --time plus film time, and timers run on
Playwright's paused clock in step with it. Output goes to a hidden sibling
file renamed onto the target only when the capture completes, so an
interrupted run leaves nothing at the target path.

Exit codes: 0 ok, 2 usage error, 3 missing dependency (Playwright,
Chromium, ffmpeg), 4 page or capture failure, 5 encoder failure.`

// What an interrupted or failed run must clean up: the partial output file
// (renamed onto the target only after a complete encode), the encoder, and
// the browser.
const state = { partial: null, encoder: null, browser: null, exiting: false, signalCode: 0 }

function removePartial() {
  if (!state.partial) return
  try { fs.rmSync(state.partial, { force: true }) } catch { /* already gone */ }
  state.partial = null
}

function fail(code, message) {
  removePartial()
  if (state.encoder) state.encoder.child.kill('SIGKILL')
  // Closing the browser on a signal makes in-flight page calls throw; that is
  // the signal's exit, not a capture failure.
  if (state.exiting) process.exit(state.signalCode)
  process.stderr.write(`capture-web: ${message}\n`)
  process.exit(code)
}

// A sibling path in the same directory, so the final rename is atomic and a
// half-written file never sits at the target path.
function partialFor(target) {
  const resolved = path.resolve(target)
  const ext = path.extname(resolved)
  return path.join(path.dirname(resolved), `.${path.basename(resolved, ext)}.partial-${process.pid}${ext}`)
}

function onSignal(code, name) {
  if (state.exiting) {
    // A second signal: stop waiting on the browser and leave now.
    removePartial()
    process.exit(code)
  }
  state.exiting = true
  state.signalCode = code
  removePartial()
  if (state.encoder) state.encoder.child.kill('SIGKILL')
  process.stderr.write(`capture-web: ${name}, stopping; no output was written\n`)
  const closing = state.browser ? state.browser.close().catch(() => {}) : Promise.resolve()
  const timer = setTimeout(() => process.exit(code), 5000)
  closing.then(() => { clearTimeout(timer); process.exit(code) })
}
process.on('SIGINT', () => onSignal(130, 'interrupted'))
process.on('SIGTERM', () => onSignal(143, 'terminated'))

function parseArgs(argv) {
  const opts = {
    seconds: 5, fps: 60, warmup: 0, at: 0, time: '2026-01-01T12:00:00Z', seed: 1,
    width: 1920, height: 1080, scale: 2, colorScheme: 'light', transparent: false,
    evals: [], presses: [], browserArgs: [], timeout: 60000, crf: 16, preset: 'medium', json: false, probe: false,
  }
  const numeric = { '--seconds': 'seconds', '--fps': 'fps', '--warmup': 'warmup', '--at': 'at',
    '--seed': 'seed', '--width': 'width', '--height': 'height', '--scale': 'scale',
    '--timeout': 'timeout', '--crf': 'crf' }
  const text = { '--url': 'url', '--out': 'out', '--frames': 'frames', '--still': 'still',
    '--time': 'time', '--color-scheme': 'colorScheme', '--preset': 'preset' }
  // Accept --name=value as well as --name value.
  argv = argv.flatMap((a) => (/^--[a-z-]+=/.test(a) ? [a.slice(0, a.indexOf('=')), a.slice(a.indexOf('=') + 1)] : [a]))
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i]
    const value = () => {
      const v = argv[++i]
      if (v === undefined) fail(2, `${arg} needs a value`)
      return v
    }
    if (arg === '-h' || arg === '--help') { process.stdout.write(`${HELP}\n`); process.exit(0) }
    else if (arg === '--json') opts.json = true
    else if (arg === '--probe') opts.probe = true
    else if (arg === '--transparent') opts.transparent = true
    else if (arg === '--eval') opts.evals.push(value())
    else if (arg === '--press') opts.presses.push(value())
    else if (arg === '--browser-arg') opts.browserArgs.push(value())
    else if (arg in numeric) {
      const v = Number(value())
      if (!Number.isFinite(v)) fail(2, `${arg} takes a number`)
      opts[numeric[arg]] = v
    } else if (arg in text) opts[text[arg]] = value()
    else fail(2, `unknown option ${arg} (see --help)`)
  }
  return opts
}

function findVersion(resolved) {
  let dir = path.dirname(resolved)
  for (let i = 0; i < 6; i++) {
    const pkg = path.join(dir, 'package.json')
    if (fs.existsSync(pkg)) {
      try {
        const meta = JSON.parse(fs.readFileSync(pkg, 'utf8'))
        if (meta.name === 'playwright' || meta.name === 'playwright-core') return meta.version
      } catch { /* keep walking */ }
    }
    dir = path.dirname(dir)
  }
  return 'unknown'
}

function loadPlaywright() {
  const require = createRequire(path.join(process.cwd(), 'demo-reel-resolve.cjs'))
  const names = []
  if (process.env.DEMO_REEL_PLAYWRIGHT) names.push(path.resolve(process.env.DEMO_REEL_PLAYWRIGHT))
  names.push('playwright', 'playwright-core')
  for (const name of names) {
    try {
      const resolved = require.resolve(name)
      const mod = require(resolved)
      if (mod && mod.chromium) return { mod, resolved, version: findVersion(resolved) }
    } catch { /* try the next candidate */ }
  }
  return null
}

// Runs in every frame before any page script. Seeds Math.random and takes
// over requestAnimationFrame and performance.now(), so rAF-driven drawing
// advances exactly once per film frame. __filmStep(now) flushes the frame's
// rAF callbacks, then pins every CSS and Web Animation to film time.
//
// Playwright's fake clock fires rAF on its own performance timeline, which
// sat 0 to 2 ms away from the paused Date.now() and varied from run to run;
// owning rAF here removes that drift.
function filmInit({ seed, origin }) {
  let s = seed >>> 0 || 0x9e3779b9
  Math.random = () => {
    s ^= s << 13
    s ^= s >>> 17
    s ^= s << 5
    return (s >>> 0) / 4294967296
  }
  const film = { seen: new WeakMap(), now: origin, prev: origin }
  const frameCallbacks = new Map()
  let nextHandle = 1
  Object.defineProperty(window, '__film', { value: film })
  performance.now = () => film.now
  window.requestAnimationFrame = (callback) => {
    const handle = nextHandle++
    frameCallbacks.set(handle, callback)
    return handle
  }
  window.cancelAnimationFrame = (handle) => {
    frameCallbacks.delete(handle)
  }
  window.__filmStep = (now) => {
    film.prev = film.now
    film.now = now
    const callbacks = [...frameCallbacks.values()]
    frameCallbacks.clear()
    for (const callback of callbacks) {
      try {
        callback(now)
      } catch (error) {
        if (typeof reportError === 'function') reportError(error)
      }
    }
    for (const animation of document.getAnimations()) {
      // An animation first seen now started somewhere in the last step; treat
      // it as starting at the step's beginning so every run agrees.
      if (!film.seen.has(animation)) {
        animation.pause()
        film.seen.set(animation, film.prev)
      }
      animation.currentTime = film.now - film.seen.get(animation)
    }
  }
}

function toUrl(raw) {
  if (/^[a-z][a-z0-9+.-]*:/i.test(raw)) return raw
  // A local path may carry a #fragment for pages that read their settings
  // from location.hash, such as assets/card.html and assets/timer.html.
  const cut = raw.indexOf('#')
  const file = path.resolve(cut === -1 ? raw : raw.slice(0, cut))
  if (!fs.existsSync(file)) fail(2, `no such file: ${file}`)
  return pathToFileURL(file).href + (cut === -1 ? '' : raw.slice(cut))
}

async function probe() {
  const pw = loadPlaywright()
  if (!pw) {
    process.stdout.write(`${JSON.stringify({ playwright: null })}\n`)
    return
  }
  let launch = 'ok'
  try {
    const browser = await pw.mod.chromium.launch({ headless: true, timeout: 30000 })
    await browser.close()
  } catch (error) {
    launch = String(error && error.message ? error.message : error).split('\n')[0]
  }
  process.stdout.write(`${JSON.stringify({ playwright: pw.resolved, version: pw.version, launch })}\n`)
}

function startEncoder(opts, target) {
  const vf = [
    'scale=out_color_matrix=bt709:out_range=tv',
    'format=yuv420p',
    // Write the color tags into the stream itself; ffmpeg's -color_* output
    // options alone did not reach the bitstream in testing.
    'setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv',
  ].join(',')
  const args = ['-nostdin', '-hide_banner', '-loglevel', 'error', '-y',
    '-f', 'image2pipe', '-c:v', 'png', '-framerate', String(opts.fps), '-i', 'pipe:0',
    '-vf', vf, '-c:v', 'libx264', '-preset', opts.preset, '-crf', String(opts.crf),
    '-movflags', '+faststart', target]
  const child = spawn('ffmpeg', args, { stdio: ['pipe', 'ignore', 'pipe'] })
  let stderr = ''
  child.stderr.on('data', (chunk) => { stderr += chunk })
  const done = new Promise((resolve) => {
    child.on('error', (error) => resolve({ code: -1, stderr: String(error.message) }))
    child.on('close', (code) => resolve({ code, stderr }))
  })
  return { child, done }
}

async function main() {
  const opts = parseArgs(process.argv.slice(2))
  if (opts.probe) return probe()

  const outputs = ['out', 'frames', 'still'].filter((k) => opts[k])
  if (!opts.url) fail(2, '--url is required')
  if (outputs.length !== 1) fail(2, 'choose exactly one of --out, --frames, --still')
  if (opts.transparent && opts.out) fail(2, '--transparent needs --frames or --still (MP4 has no alpha)')
  if (!(opts.fps > 0 && opts.fps <= 240)) fail(2, '--fps must be between 1 and 240')
  if (!(opts.seconds > 0)) fail(2, '--seconds must be positive')
  if (!['light', 'dark', 'no-preference'].includes(opts.colorScheme)) fail(2, '--color-scheme takes light or dark')
  const pixelWidth = Math.round(opts.width * opts.scale)
  const pixelHeight = Math.round(opts.height * opts.scale)
  if (opts.out && (pixelWidth % 2 || pixelHeight % 2)) {
    fail(2, `frames would be ${pixelWidth}x${pixelHeight}; yuv420p needs even dimensions`)
  }
  const startTime = new Date(opts.time)
  if (Number.isNaN(startTime.getTime())) fail(2, `--time is not a date: ${opts.time}`)
  // Inputs before dependencies: a missing page is a usage error, not a
  // missing Playwright.
  const url = toUrl(opts.url)

  const pw = loadPlaywright()
  if (!pw) {
    fail(3, 'playwright not found. Install it in the project (npm install --save-dev playwright) '
      + 'or set DEMO_REEL_PLAYWRIGHT to an installed playwright package, then run npx playwright install chromium')
  }

  let browser
  try {
    // Playwright's own signal handlers are off; onSignal closes the browser.
    browser = await pw.mod.chromium.launch({
      headless: true, args: opts.browserArgs,
      handleSIGINT: false, handleSIGTERM: false, handleSIGHUP: false,
    })
    state.browser = browser
  } catch (error) {
    fail(3, `Chromium did not launch (${String(error.message).split('\n')[0]}). Run: npx playwright install chromium`)
  }

  const started = Date.now()
  const digest = createHash('sha256')
  let encoder = null
  let frames = 0
  try {
    const context = await browser.newContext({
      viewport: { width: opts.width, height: opts.height },
      deviceScaleFactor: opts.scale,
      colorScheme: opts.colorScheme,
      locale: 'en-US',
      timezoneId: 'UTC',
      reducedMotion: 'no-preference',
    })
    const page = await context.newPage()
    // Wait for the GPU process before the page creates its canvases. A
    // canvas created while it is still starting shows a blank white
    // placeholder for its first frames; a delayed GPU launcher reproduced it.
    // A WebGL readback blocks until the GPU channel is up.
    await page.evaluate(() => {
      const gl = document.createElement('canvas').getContext('webgl')
      if (!gl) return false
      gl.clearColor(0, 0, 0, 1)
      gl.clear(gl.COLOR_BUFFER_BIT)
      gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array(4))
      return true
    })
    // Page load happens one frame before film zero: that frame is the
    // discarded pre-roll below, so frame i shows film time warmup + i/fps.
    // The clock starts one pre-roll earlier too, so Date.now() is always
    // --time plus film time.
    const preroll = Math.round(1000 / opts.fps)
    const clockStart = new Date(startTime.getTime() - preroll)
    await page.clock.install({ time: clockStart })
    // Registered after the clock so these rAF and performance.now() win.
    await page.addInitScript(filmInit, { seed: opts.seed, origin: -preroll })
    // An installed clock still flows with real time; pause it so page load
    // speed cannot leak into JS-driven motion. Only runFor moves it now.
    await page.clock.pauseAt(clockStart)
    await page.goto(url, { waitUntil: 'load', timeout: opts.timeout })
    await page.evaluate(() => (document.fonts ? document.fonts.ready.then(() => true) : true))

    let film = -preroll
    const step = async (ms) => {
      if (ms > 0) await page.clock.runFor(ms)
      film += ms
      for (const frame of page.frames()) {
        // Cross-origin frames reject evaluate; they are documented as unsupported.
        await frame.evaluate((now) => window.__filmStep && window.__filmStep(now), film).catch(() => {})
      }
    }
    for (let t = 0; t < opts.warmup; t += 100) await step(Math.min(100, opts.warmup - t))
    await step(0)
    for (const js of opts.evals) await page.evaluate(js)
    for (const key of opts.presses) await page.keyboard.press(key)

    const shoot = () => page.screenshot({ type: 'png', omitBackground: opts.transparent, timeout: 30000 })
    // The first raster after an animation is pinned differed by a sub-pixel
    // between runs, even with identical animation state on the main thread.
    // Pre-roll one discarded frame so frame 0 is a settled frame.
    await step(preroll)
    await shoot()
    const frameTime = (i) => Math.round((i * 1000) / opts.fps)
    let last = 0
    const advanceTo = async (i) => {
      const target = frameTime(i)
      await step(target - last)
      last = target
    }

    if (opts.still) {
      const index = Math.round((opts.at * opts.fps) / 1000)
      for (let i = 0; i <= index; i++) await advanceTo(i)
      const buffer = await shoot()
      fs.mkdirSync(path.dirname(path.resolve(opts.still)), { recursive: true })
      state.partial = partialFor(opts.still)
      fs.writeFileSync(state.partial, buffer)
      fs.renameSync(state.partial, opts.still)
      state.partial = null
      digest.update(buffer)
      frames = 1
    } else {
      const total = Math.round(opts.seconds * opts.fps)
      if (opts.frames) fs.mkdirSync(opts.frames, { recursive: true })
      if (opts.out) {
        fs.mkdirSync(path.dirname(path.resolve(opts.out)), { recursive: true })
        state.partial = partialFor(opts.out)
        encoder = startEncoder(opts, state.partial)
        state.encoder = encoder
      }
      for (let i = 0; i < total; i++) {
        await advanceTo(i)
        const buffer = await shoot()
        digest.update(buffer)
        frames++
        if (opts.frames) {
          fs.writeFileSync(path.join(opts.frames, `${String(i).padStart(5, '0')}.png`), buffer)
        } else if (!encoder.child.stdin.write(buffer)) {
          const drained = once(encoder.child.stdin, 'drain')
          const exited = encoder.done.then(() => { throw new Error('ffmpeg exited during capture') })
          await Promise.race([drained, exited])
        }
      }
    }
  } catch (error) {
    await browser.close().catch(() => {})
    if (encoder) encoder.child.kill('SIGKILL')
    fail(4, `capture failed: ${String(error && error.message ? error.message : error).split('\n')[0]}`)
  }
  await browser.close().catch(() => {})

  if (encoder) {
    encoder.child.stdin.end()
    const result = await encoder.done
    if (result.code !== 0) {
      const hint = result.code === -1 ? ' (is ffmpeg on PATH?)' : ''
      fail(result.code === -1 ? 3 : 5, `ffmpeg failed${hint}: ${result.stderr.trim().slice(0, 400)}`)
    }
    state.encoder = null
    fs.renameSync(state.partial, opts.out)
    state.partial = null
  }

  const summary = {
    url, out: opts.out || null, frames_dir: opts.frames || null, still: opts.still || null,
    frames, fps: opts.fps, width: pixelWidth, height: pixelHeight,
    film_seconds: opts.still ? opts.at / 1000 : frames / opts.fps,
    seed: opts.seed, digest: digest.digest('hex'), elapsed_ms: Date.now() - started,
    playwright: pw.version,
  }
  if (opts.json) process.stdout.write(`${JSON.stringify(summary)}\n`)
  else {
    const target = opts.out || opts.frames || opts.still
    process.stderr.write(`capture-web: ${frames} frame(s) at ${pixelWidth}x${pixelHeight} -> ${target} `
      + `in ${(summary.elapsed_ms / 1000).toFixed(1)}s (digest ${summary.digest.slice(0, 12)})\n`)
  }
}

main().catch((error) => fail(4, String(error && error.stack ? error.stack : error)))
