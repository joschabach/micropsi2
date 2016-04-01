

// thanks to Chris Coyier at css-tricks.com
jQuery.fn.putCursorAtEnd = function() {
    return this.each(function() {
        $(this).focus()
        // If this function exists...
        if (this.setSelectionRange) {
            // ... then use it (Doesn't work in IE)
            // Double the length because Opera is inconsistent about whether a carriage return is one character or two. Sigh.
            var len = $(this).val().length * 2;
            this.setSelectionRange(len, len);
        } else {
            // ... otherwise replace the contents with itself
            // (Doesn't work in Google Chrome)
            $(this).val($(this).val());
        }
        // Scroll to the bottom, in case we're in a tall textarea
        // (Necessary for Firefox and Google Chrome)
        this.scrollTop = 999999;
    });
};

function registerResizeHandler(){
    // resize handler for nodenet viewer:
    var isDragging = false;
    var container = $('#netapi_console .code_container');
    if($.cookie('netapi_console_height')){
        container.height($.cookie('netapi_console_height'));
    }
    var startHeight, startPos, newHeight;
    $("a#consoleSizeHandle").mousedown(function(event) {
        startHeight = container.height();
        startPos = event.pageY;
        $(window).mousemove(function(event) {
            isDragging = true;
            newHeight = startHeight + (event.pageY - startPos);
            container.height(newHeight);
        });
    });
    $(window).mouseup(function(event) {
        if(isDragging){
            $.cookie('netapi_console_height', container.height(), {expires:7, path:'/'});
        }
        isDragging = false;
        $(window).unbind("mousemove");
    });
}

$(function(){

    var input = $('#console_input');
    var currentNodenet = '';
    var cookieval = $.cookie('selected_nodenet');
    if (cookieval && cookieval.indexOf('/')){
        currentNodenet = cookieval.split('/')[0];
    }

    var history = $('#console_history');
    var container = $('#netapi_console .code_container');

    hljs.highlightBlock(history[0]);

    command_history = [];
    history_pointer = -1;

    registerResizeHandler();

    input.keydown(function(event){
        var code = input.val();
        if(event.keyCode == 13){
            api.call('run_netapi_command', {nodenet_uid: currentNodenet, command: code}, function(data){
                data = data.replace(/\n+/g, '\n')
                var hist = history.text();
                hist += "\n" + ">>> " + code;
                if(data){
                    hist += "\n" + data;
                }
                history.text(hist);
                input.val('');
                hljs.highlightBlock(history[0]);
                container.scrollTop(999999999)
                command_history.push(code);
                $(document).trigger('runner_stepped');
            }, function(error){
                var hist = history.text();
                if(error.data){
                    hist += "\n" + ">>> " + code;
                    hist += '\nERROR: '+error.data;
                }
                history.text(hist);
                input.val('');
                hljs.highlightBlock(history[0]);
                container.scrollTop(999999999)
                command_history.push(code);
            });
        }
        if(event.keyCode == 38){
            // arrow up
            if(code == '' && history_pointer == -1){
                event.preventDefault();
                history_pointer = command_history.length - 1;
                input.val(command_history[history_pointer])
                input.putCursorAtEnd()
            } else if(history_pointer > 0 && code == command_history[history_pointer]) {
                event.preventDefault();
                history_pointer -= 1;
                input.val(command_history[history_pointer])
                input.putCursorAtEnd()
            }
        } else if(event.keyCode == 40){
            // arrow down
            if(history_pointer < command_history.length - 1 && code == command_history[history_pointer]) {
                event.preventDefault();
                history_pointer += 1;
                input.val(command_history[history_pointer])
                input.putCursorAtEnd()
            }
        }
        else {
            history_pointer = -1
        }
    })

});

