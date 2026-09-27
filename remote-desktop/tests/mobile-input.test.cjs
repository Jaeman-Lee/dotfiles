const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

function harness() {
    const calls = [], timers = [], listeners = {};
    const element = {addEventListener() {}, removeEventListener() {}, focus() {}};
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
            directive = deps.at(-1)({navigator: {maxTouchPoints: 1}, document: {}}, timeout);
        }})},
        Guacamole: {StringWriter: function () {
            this.sendText = text => calls.push(['clipboard', text]);
            this.sendEnd = () => calls.push(['end']);
        }}
    });
    directive.link(scope, [{querySelector: () => element}]);
    return {scope, calls, listeners, step() {
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
    assert.equal(h.scope.draft, '한글 hello');
});
test('manual paste then Enter does not paste the draft twice', () => {
    const h = harness(); h.scope.draft = 'one';
    h.scope.pasteDraft(false); h.step(); h.scope.sendEnter();
    assert.equal(h.calls.filter(c => c[0] === 'clipboard').length, 1);
    assert.deepEqual(h.calls.slice(-2), enter);
    h.scope.draftEdited(); h.scope.sendEnter();
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
});
test('leaving the view cancels pending Enter', () => {
    const h = harness(); h.scope.draft = 'do not execute';
    h.scope.sendEnter(); h.step(); h.listeners.$destroy(); h.step();
    assert.equal(h.calls.some(c => c[2] === 0xff0d), false);
});
