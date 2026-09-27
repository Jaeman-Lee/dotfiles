/* Guacamole 1.6.0 UI extension. Draft text stays in memory for this view only. */
angular.module('client').directive('ubuntuMobileInput', ['$window', '$timeout', function ($window, $timeout) {
    return {
        restrict: 'E',
        scope: true,
        link: function (scope, element) {
            // Include iPad with an attached keyboard/desktop browser identity.
            scope.writing = $window.navigator.maxTouchPoints > 0;
            scope.draft = '';
            scope.terminal = false;
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

            var pendingPaste;
            scope.pasteDraft = function () {
                var managed = scope.focusedClient;
                if (!scope.draft || scope.sending) return;
                if (!managed || managed.clientState.connectionState !== 'CONNECTED') {
                    scope.notice = 'PC 연결을 확인한 뒤 다시 눌러 주세요.';
                    return;
                }
                scope.sending = true;
                var client = managed.client;
                var terminal = scope.terminal;
                var writer = new Guacamole.StringWriter(client.createClipboardStream('text/plain'));
                writer.onack = function (status) {
                    if (status.isError()) {
                        $timeout.cancel(pendingPaste);
                        scope.$evalAsync(function () {
                            scope.sending = false;
                            scope.notice = 'PC 클립보드로 보내지 못했습니다. 연결을 확인하세요.';
                        });
                    }
                };
                writer.sendText(scope.draft);
                writer.sendEnd();
                // GNOME receives the clipboard asynchronously after the RDP
                // stream closes. Retain the draft: sending a shortcut does not
                // acknowledge insertion into the user's chosen application.
                pendingPaste = $timeout(function () {
                    scope.sending = false;
                    if (scope.focusedClient !== managed || managed.clientState.connectionState !== 'CONNECTED') {
                        scope.notice = '연결이 바뀌었습니다. 입력할 곳을 선택하고 다시 눌러 주세요.';
                        return;
                    }
                    client.sendKeyEvent(1, 0xFFE3);
                    if (terminal) client.sendKeyEvent(1, 0xFFE1);
                    client.sendKeyEvent(1, 0x76);
                    client.sendKeyEvent(0, 0x76);
                    if (terminal) client.sendKeyEvent(0, 0xFFE1);
                    client.sendKeyEvent(0, 0xFFE3);
                    scope.notice = '붙여넣기를 요청했습니다. PC 화면에서 확인하세요.';
                }, 500);
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
                scope.draft = '';
            });
        }
    };
}]);
