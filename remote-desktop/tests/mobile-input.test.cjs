const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

function harness() {
    const calls = [], timers = [], listeners = {};
    const documentListeners = {};
    const document = {
        activeElement: null,
        addEventListener(name, fn) { documentListeners[name] = fn; },
        removeEventListener(name) { delete documentListeners[name]; },
        getElementById() { return remote; }
    };
    function node(id) {
        const events = {};
        return {
            id, tagName: 'TEXTAREA', events,
            addEventListener(name, fn) { events[name] = fn; },
            removeEventListener(name) { delete events[name]; },
            focus() { document.activeElement = this; },
            getBoundingClientRect() { return {width: 100, height: 70}; },
            fire(type, options = {}) {
                const event = {type, defaultPrevented: false, stopped: false,
                    preventDefault() { this.defaultPrevented = true; },
                    stopPropagation() { this.stopped = true; }, ...options};
                if (events[type]) events[type](event);
                return event;
            }
        };
    }
    const draft = node('ubuntu-writing-text'), writing = node('writing'),
        keyboard = node('keyboard'), remote = node('ubuntu-remote-text');
    const nodes = {'#ubuntu-writing-text': draft, '.ubuntu-open-writing': writing,
        '.ubuntu-open-keyboard': keyboard};
    const scope = {
        menu: {},
        $on(name, fn) { listeners[name] = fn; },
        $apply(fn) { fn(); }, $evalAsync(fn) { fn(); }
    };
    scope.focusedClient = {clientState: {connectionState: 'CONNECTED'}, client: {
        createClipboardStream() { return {}; },
        sendKeyEvent(down, key) { calls.push(['key', down, key]); }
    }};
    const timeout = (fn, ms) => { const timer = {fn, ms}; timers.push(timer); return timer; };
    timeout.cancel = timer => { if (timer) timer.cancelled = true; };
    let directive;
    vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../mobile-input/mobile-input.js'), 'utf8'), {
        angular: {module: () => ({directive: (name, deps) => {
            directive = deps.at(-1)({navigator: {maxTouchPoints: 1}, document}, timeout);
        }})},
        Guacamole: {StringWriter: function () {
            this.sendText = text => calls.push(['clipboard', text]);
            this.sendEnd = () => calls.push(['end']);
        }}
    });
    directive.link(scope, [{querySelector: selector => nodes[selector]}]);
    return {scope, calls, listeners, draft, writing, keyboard, remote, document, documentListeners, step() {
        const timer = timers.shift();
        if (timer && !timer.cancelled) timer.fn();
    }};
}
const enter = [['key', 1, 0xff0d], ['key', 0, 0xff0d]];

test('Enter with a draft pastes before sending Enter, blocking double taps', () => {
    const h = harness(); h.scope.draft = '한글 hello';
    h.scope.sendEnter(); h.scope.sendEnter();
    assert.deepEqual(h.calls, [['clipboard', '한글 hello'], ['end']]);
    h.step();
    assert.equal(h.calls.some(c => c[2] === 0xff0d), false);
    assert.equal(h.scope.sending, true);
    h.step();
    assert.deepEqual(h.calls.slice(-2), enter);
    assert.equal(h.scope.sending, false);
    assert.equal(h.scope.draft, '');
});
test('manual paste then Enter does not paste the draft twice', () => {
    const h = harness(); h.scope.draft = 'one';
    h.scope.pasteDraft(false); h.step();
    assert.equal(h.scope.draft, 'one');
    h.scope.sendEnter();
    assert.equal(h.calls.filter(c => c[0] === 'clipboard').length, 1);
    assert.deepEqual(h.calls.slice(-2), enter);
    h.scope.draft = 'one'; h.scope.draftEdited(); h.scope.sendEnter();
    assert.equal(h.calls.filter(c => c[0] === 'clipboard').length, 2);
});
test('default send uses terminal paste without requiring a checkbox', () => {
    const h = harness(); h.scope.draft = '안녕';
    assert.equal(h.scope.terminal, true);
    h.scope.sendEnter(); h.step(); h.step();
    assert.deepEqual(h.calls.slice(2), [
        ['key',1,0xffe3], ['key',1,0xffe1], ['key',1,86], ['key',0,86],
        ['key',0,0xffe1], ['key',0,0xffe3], ...enter
    ]);
});
test('general app paste is available only after explicit selection', () => {
    const h = harness(); h.scope.draft = '안녕'; h.scope.terminal = false;
    h.scope.pasteDraft(false); h.step();
    assert.deepEqual(h.calls.slice(2), [
        ['key',1,0xffe3], ['key',1,118], ['key',0,118], ['key',0,0xffe3]
    ]);
});
test('empty draft and collapsed writing send only Enter', () => {
    for (const writing of [true, false]) {
        const h = harness(); h.scope.writing = writing;
        if (!writing) h.scope.draft = 'hidden draft';
        h.scope.sendEnter(); assert.deepEqual(h.calls, enter);
    }
});
test('disconnect between paste and Enter cancels execution', () => {
    const h = harness(); h.scope.draft = 'do not execute';
    h.scope.sendEnter(); h.step();
    h.scope.focusedClient.clientState.connectionState = 'DISCONNECTED'; h.step();
    assert.equal(h.calls.some(c => c[2] === 0xff0d), false);
    assert.equal(h.scope.draft, 'do not execute');
});
test('submit preserves a new draft written during the paste delay', () => {
    const h = harness(); h.scope.draft = 'first'; h.scope.sendEnter();
    h.scope.draft = 'next'; h.scope.draftEdited(); h.step(); h.step();
    assert.equal(h.scope.draft, 'next');
});
test('submit preserves a newly edited draft even if its text is identical', () => {
    const h = harness(); h.scope.draft = 'repeat'; h.scope.sendEnter();
    h.scope.draftEdited(); h.step(); h.step();
    assert.equal(h.scope.draft, 'repeat');
});
test('leaving the view cancels pending Enter', () => {
    const h = harness(); h.scope.draft = 'do not execute';
    h.scope.sendEnter(); h.step(); h.listeners.$destroy(); h.step();
    assert.equal(h.calls.some(c => c[2] === 0xff0d), false);
});

test('opening writing restores the local draft focus', () => {
    const h = harness(); h.scope.writing = false; h.scope.menu.inputMethod = 'text';
    h.remote.focus(); h.writing.fire('click');
    assert.equal(h.scope.writing, true);
    assert.equal(h.scope.menu.inputMethod, 'none');
    assert.equal(h.document.activeElement, h.draft);
});
test('writing blocks remote capture even after draft loses focus', () => {
    const h = harness(); h.document.activeElement = h.remote;
    for (const name of ['guacBeforeKeydown', 'guacBeforeKeyup']) {
        let prevented = false;
        h.listeners[name]({preventDefault() { prevented = true; }});
        assert.equal(prevented, true);
    }
    assert.deepEqual(h.calls, []);
});
test('hidden sink and legacy textarea cannot steal writing focus', () => {
    const h = harness();
    for (const target of [h.remote, {tagName: 'TEXTAREA',
        getBoundingClientRect() { return {width: 0, height: 0}; }}]) {
        h.document.activeElement = target;
        let stopped = false;
        h.documentListeners.focus({target, stopImmediatePropagation() { stopped = true; }});
        assert.equal(stopped, true);
        assert.equal(h.document.activeElement, h.draft);
    }
    const select = {tagName: 'SELECT'};
    h.document.activeElement = select; h.documentListeners.focus({target: select});
    assert.equal(h.document.activeElement, select);
});
test('collapsing or selecting legacy keyboard restores direct input', () => {
    const h = harness();
    // ng-if calls the inherited function from a child scope.
    const child = Object.create(h.scope); child.closeWriting();
    assert.equal(h.scope.writing, false);
    h.document.activeElement = h.remote;
    let prevented = false;
    h.listeners.guacBeforeKeydown({preventDefault() { prevented = true; }});
    assert.equal(prevented, false);
    h.scope.writing = true; h.keyboard.fire('click');
    assert.equal(h.scope.writing, false);
    assert.equal(h.document.activeElement, h.remote);
});
test('Ctrl+Enter sends once and retains ordinary Enter for local newlines', () => {
    const h = harness(); h.scope.draft = '한글 shortcut';
    const newline = h.draft.fire('keydown', {key: 'Enter'});
    assert.equal(newline.defaultPrevented, false);
    assert.equal(newline.stopped, true);
    assert.deepEqual(h.calls, []);
    const shortcut = h.draft.fire('keydown', {key: 'Enter', ctrlKey: true});
    assert.equal(shortcut.defaultPrevented, true);
    h.draft.fire('keydown', {key: 'Enter', ctrlKey: true});
    h.step(); h.step();
    assert.equal(h.calls.filter(c => c[0] === 'clipboard').length, 1);
    assert.deepEqual(h.calls.slice(-2), enter);
    assert.equal(h.document.activeElement, h.draft);
});
test('Ctrl+Enter never sends while IME is composing or on key repeat', () => {
    const h = harness(); h.scope.draft = '조합 중';
    h.draft.fire('compositionstart');
    h.draft.fire('keydown', {key: 'Enter', ctrlKey: true});
    h.draft.fire('compositionend');
    for (const options of [{isComposing: true}, {keyCode: 229}, {repeat: true}])
        h.draft.fire('keydown', {key: 'Enter', ctrlKey: true, ...options});
    assert.deepEqual(h.calls, []);
    h.draft.fire('keydown', {key: 'Enter', ctrlKey: true});
    assert.equal(h.calls[0][0], 'clipboard');
});
test('empty Ctrl+Enter does not execute the remote prompt', () => {
    const h = harness();
    assert.equal(h.draft.fire('keydown', {key: 'Enter', ctrlKey: true}).defaultPrevented, true);
    assert.deepEqual(h.calls, []);
});
test('focus protection is removed when the view is destroyed', () => {
    const h = harness(); h.listeners.$destroy();
    assert.equal(h.documentListeners.focus, undefined);
    assert.deepEqual(Object.keys(h.draft.events), []);
});
