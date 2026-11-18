import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import vm from 'node:vm'

const source = readFileSync(new URL('../src/views/FastActionTestView.vue', import.meta.url), 'utf8')
const script = source.match(/<script setup>([\s\S]*?)<\/script>/)[1]
function blockAt(start) {
  const open = script.indexOf('{', start)
  let depth = 1, end = open + 1
  while (depth && end < script.length) {
    if (script[end] === '{') depth++
    if (script[end] === '}') depth--
    end++
  }
  return script.slice(start, end)
}
const names = ['startVoiceRecording', 'stopVoiceRecording', 'stopStreamTracks', 'stopVoiceTracks', 'cleanupVoiceRecording', 'handleVoiceRecordingStopped', 'setupPhoneScaleObserver']
const functions = names.map(name => blockAt(script.search(new RegExp(`(?:async )?function ${name}\\(`)))).join('\n')
const hook = name => blockAt(script.indexOf(name + '(')).replace(name + '(', '').trim()
const deferred = () => { let resolve, reject; const promise = new Promise((a, b) => { resolve = a; reject = b }); return { promise, resolve, reject } }

function fixture({ fail = '', mountGate = -1 } = {}) {
  const requests = [], streams = [], timers = new Map(), listeners = new Set(), recorders = []
  let tracks = 0, observers = 0, asr = 0, loads = 0, revokeCalls = 0
  const gate = deferred()
  const load = async () => { if (loads++ === mountGate) await gate.promise }
  class Recorder {
    constructor() { if (fail === 'constructor') throw Error('constructor failed'); this.state = 'inactive'; this.mimeType = 'audio/webm'; recorders.push(this) }
    start() { if (fail === 'start') throw Error('start failed'); this.state = 'recording' }
    stop() { if (fail === 'stop') throw Error('stop failed'); this.state = 'inactive'; this.onstop?.() }
  }
  const scope = {
    navigator: { mediaDevices: { getUserMedia() { const request = deferred(); requests.push(request); return request.promise } } },
    window: { MediaRecorder: Recorder, setTimeout(fn, ms) { const id = timers.size + 1; timers.set(id, { fn, ms }); return id }, clearTimeout(id) { timers.delete(id) }, addEventListener(type, fn) { listeners.add(fn) }, removeEventListener(type, fn) { listeners.delete(fn) } },
    ResizeObserver: class { constructor() { observers++ } observe() {} disconnect() { observers-- } },
    composerNotice: { value: '' }, isRecording: { value: false }, voiceBusy: { value: false }, testInput: { value: '' }, voiceSupported: { value: false },
    selectedAttachments: { value: [] }, chatMessages: { value: [] }, previewStageRef: { value: {} },
    updatePreviewLayout() {}, stopPreviewResize() {}, revokeAttachments() { revokeCalls++ }, hasVoiceRecordingSupport: () => true,
    loadSettings: load, loadPersistedTestMessages: load, refreshTestRecords: load, nextTick: load, scrollPreviewContainersToBottom() {},
    transcribeFastActionAudio: async () => { asr++; return { text: '合成转写' } }, Blob, File: class extends Blob {},
  }
  vm.createContext(scope)
  vm.runInContext(`let componentDisposed = false, recordingGeneration = 0, mediaRecorder = null, mediaStream = null, recordingTimer = null, audioChunks = [], previewResizeObserver = null;\n${functions}\nglobalThis.actions = {startVoiceRecording,stopVoiceRecording,cleanupVoiceRecording,mount:${hook('onMounted')},unmount:${hook('onBeforeUnmount')}}`, scope)
  const grant = index => {
    const track = { live: true, stop() { if (this.live) { this.live = false; tracks-- } } }
    const stream = { getTracks: () => [track] }; streams.push(stream); tracks++; requests[index].resolve(stream)
  }
  return { scope, grant, requests, recorders, timers, streams, gate, actions: scope.actions, state: () => ({ tracks, timers: timers.size, listeners: listeners.size, observers, asr, loads, revokeCalls }) }
}

test('normal recording retains original 60s cutoff and releases on stop', async () => {
  const f = fixture(); const pending = f.actions.startVoiceRecording(); f.grant(0); await pending
  assert.equal(f.state().tracks, 1); assert.equal([...f.timers.values()][0].ms, 60000)
  f.actions.stopVoiceRecording()
  assert.equal(f.state().tracks, 0); assert.equal(f.state().timers, 0); assert.equal(f.state().asr, 0)
})
for (const fail of ['constructor', 'start']) test(`${fail} failure releases the granted stream and keeps original error`, async () => {
  const f = fixture({ fail }); const pending = f.actions.startVoiceRecording(); f.grant(0); await pending
  assert.equal(f.state().tracks, 0); assert.equal(f.state().timers, 0)
  assert.equal(f.scope.composerNotice.value, `${fail} failed`)
  for (const r of f.recorders) { assert.equal(r.onstop, null); assert.equal(r.ondataavailable, null) }
})
test('late permission after unmount stops tracks without creating recorder or timer', async () => {
  const f = fixture(); const pending = f.actions.startVoiceRecording(); f.actions.unmount(); f.grant(0); await pending
  assert.equal(f.state().tracks, 0); assert.equal(f.state().timers, 0); assert.equal(f.recorders.length, 0); assert.equal(f.state().asr, 0)
})
test('late denied permission after unmount does not write a stale notice', async () => {
  const f = fixture(); const pending = f.actions.startVoiceRecording(); f.actions.unmount(); f.requests[0].reject(Error('late permission')); await pending
  assert.equal(f.scope.composerNotice.value, ''); assert.equal(f.state().tracks, 0)
})
test('out-of-order overlapping grants keep only the latest acquisition', async () => {
  const f = fixture(); const first = f.actions.startVoiceRecording(); const second = f.actions.startVoiceRecording(); f.grant(1); await second; f.grant(0); await first
  assert.equal(f.state().tracks, 1); assert.equal(f.recorders.length, 1); assert.equal(f.state().timers, 1)
  f.actions.unmount(); assert.equal(f.state().tracks, 0); assert.equal(f.state().timers, 0)
})
test('throwing recorder stop cannot prevent unmount from releasing all owners', async () => {
  const f = fixture({ fail: 'stop' }); const pending = f.actions.startVoiceRecording(); f.grant(0); await pending; f.actions.unmount()
  assert.equal(f.state().tracks, 0); assert.equal(f.state().timers, 0); assert.equal(f.state().revokeCalls, 2)
})
test('ordinary stop failure still releases its tracks before propagating the error', async () => {
  const f = fixture({ fail: 'stop' }); const pending = f.actions.startVoiceRecording(); f.grant(0); await pending
  assert.throws(() => f.actions.stopVoiceRecording(), /stop failed/)
  assert.equal(f.state().tracks, 0); assert.equal(f.state().timers, 0)
})
for (let mountGate = 0; mountGate < 4; mountGate++) test(`unmount during mount await ${mountGate + 1} cannot register late observers`, async () => {
  const f = fixture({ mountGate }); const pending = f.actions.mount()
  for (let n = 0; f.state().loads <= mountGate && n < 20; n++) await Promise.resolve()
  f.actions.unmount(); f.gate.resolve(); await pending
  assert.equal(f.state().listeners, 0); assert.equal(f.state().observers, 0)
})
test('normal mounted observer and resize listener are still installed then removed', async () => {
  const f = fixture(); await f.actions.mount(); assert.equal(f.state().listeners, 1); assert.equal(f.state().observers, 1)
  f.actions.unmount(); assert.equal(f.state().listeners, 0); assert.equal(f.state().observers, 0)
})
