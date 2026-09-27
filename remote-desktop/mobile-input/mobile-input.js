/* Guacamole 1.6.0 UI extension. Draft text stays in memory for this view only. */
angular.module('client').directive('ubuntuMobileInput', ['$window', '$timeout', function ($window, $timeout) {
    return {
        restrict: 'E',
        scope: true,
        link: function (scope, element) {
            // Include iPad with an attached keyboard/desktop browser identity.
            scope.writing = $window.navigator.maxTouchPoints > 0;
            scope.draft = '';
            // This desktop is primarily used for Codex in Ptyxis. Plain Ctrl+V
            // reaches Codex as an image-paste command, not terminal text paste.
            scope.terminal = true;
            if (scope.writing) scope.menu.inputMethod = 'none';

            var draft = element[0].querySelector('#ubuntu-writing-text');
            // The native keyboard/IME edits this local draft. Never forward its
            // physical key events to the remote client as well.
            function localKey(event) { event.stopPropagation(); }
            ['keydown', 'keyup', 'keypress'].forEach(function (name) {
                draft.addEventListener(name, localKey);
            });
            // Guacamole also observes keys during the DOM capture phase.
            // Its cancellable pre-key events are the supported way to keep
            // local form editing out of the remote desktop.
            ['guacBeforeKeydown', 'guacBeforeKeyup'].forEach(function (name) {
                scope.$on(name, function (event) {
                    if ($window.document.activeElement === draft) event.preventDefault();
                });
            });

            var writingButton = element[0].querySelector('.ubuntu-open-writing');
            function openWriting() {
                scope.$apply(function () {
                    scope.menu.shown = false;
                    scope.menu.inputMethod = 'none';
                    scope.writing = true;
                });
                draft.focus();
            }
            writingButton.addEventListener('click', openWriting);

            var pendingPaste, pendingEnter;
            var lastPaste = null;
            scope.draftEdited = function () { lastPaste = null; scope.notice = ''; };
            scope.pasteDraft = function (submit) {
                var managed = scope.focusedClient;
                if (scope.sending || (!scope.draft && !submit)) return;
                if (!managed || managed.clientState.connectionState !== 'CONNECTED') {
                    scope.notice = 'PC 연결을 확인한 뒤 다시 눌러 주세요.';
                    return;
                }
                scope.sending = true;
                var client = managed.client;
                var terminal = scope.terminal;
                var text = scope.draft;
                function stillConnected() {
                    return scope.focusedClient === managed && managed.clientState.connectionState === 'CONNECTED';
                }
                function enter() {
                    scope.sending = false;
                    if (!stillConnected()) {
                        scope.notice = '연결이 바뀌었습니다. PC 화면을 확인하세요.';
                        return;
                    }
                    client.sendKeyEvent(1, 0xFF0D);
                    client.sendKeyEvent(0, 0xFF0D);
                    scope.notice = '전송을 요청했습니다. PC 화면에서 확인하세요.';
                }
                // Enter after a manual paste must not insert the same draft twice.
                if (submit && (!text || (lastPaste && lastPaste.text === text &&
                        lastPaste.managed === managed && lastPaste.terminal === terminal))) {
                    enter();
                    return;
                }
                var writer = new Guacamole.StringWriter(client.createClipboardStream('text/plain'));
                writer.onack = function (status) {
                    if (status.isError()) {
                        $timeout.cancel(pendingPaste);
                        $timeout.cancel(pendingEnter);
                        scope.$evalAsync(function () {
                            scope.sending = false;
                            scope.notice = 'PC 클립보드로 보내지 못했습니다. 연결을 확인하세요.';
                        });
                    }
                };
                writer.sendText(text);
                writer.sendEnd();
                // GNOME receives the clipboard asynchronously after the RDP
                // stream closes. Retain the draft: sending a shortcut does not
                // acknowledge insertion into the user's chosen application.
                pendingPaste = $timeout(function () {
                    if (!stillConnected()) {
                        scope.sending = false;
                        scope.notice = '연결이 바뀌었습니다. 입력할 곳을 선택하고 다시 눌러 주세요.';
                        return;
                    }
                    client.sendKeyEvent(1, 0xFFE3);
                    if (terminal) client.sendKeyEvent(1, 0xFFE1);
                    // Guacamole's RDP keymap derives modifiers from the keysym.
                    // Lowercase v releases Shift even if we explicitly held it,
                    // delivering Ctrl+V (Codex image paste) to the terminal app.
                    var pasteKey = terminal ? 0x56 : 0x76;
                    client.sendKeyEvent(1, pasteKey);
                    client.sendKeyEvent(0, pasteKey);
                    if (terminal) client.sendKeyEvent(0, 0xFFE1);
                    client.sendKeyEvent(0, 0xFFE3);
                    lastPaste = { text: text, managed: managed, terminal: terminal };
                    if (submit) {
                        // Give the target app time to process its paste shortcut
                        // before Enter. Keep buttons disabled through both steps.
                        pendingEnter = $timeout(enter, 300);
                        return;
                    }
                    scope.sending = false;
                    scope.notice = '붙여넣기를 요청했습니다. PC 화면에서 확인하세요.';
                }, 500);
            };
            scope.sendEnter = function () {
                // Outside the writing panel, Enter remains an ordinary PC key.
                if (scope.writing) scope.pasteDraft(true);
                else if (!scope.sending && scope.focusedClient &&
                        scope.focusedClient.clientState.connectionState === 'CONNECTED') {
                    scope.focusedClient.client.sendKeyEvent(1, 0xFF0D);
                    scope.focusedClient.client.sendKeyEvent(0, 0xFF0D);
                }
            };

            var button = element[0].querySelector('.ubuntu-open-keyboard');
            function openKeyboard() {
                // Render synchronously within the tap. Deferring focus to a timer
                // can lose the user activation required by iOS keyboards.
                scope.$apply(function () {
                    scope.menu.shown = false;
                    scope.writing = false;
                    scope.menu.inputMethod = 'text';
                });
                var target = $window.document.getElementById('ubuntu-remote-text');
                if (target) target.focus();
            }
            button.addEventListener('click', openKeyboard);
            scope.$on('$destroy', function () {
                button.removeEventListener('click', openKeyboard);
                writingButton.removeEventListener('click', openWriting);
                ['keydown', 'keyup', 'keypress'].forEach(function (name) {
                    draft.removeEventListener(name, localKey);
                });
                $timeout.cancel(pendingPaste);
                $timeout.cancel(pendingEnter);
                scope.draft = '';
            });
        }
    };
}]);
