

// thanks to Chris Coyier at css-tricks.com
jQuery.fn.putCursorAt = function(index) {
    return this.each(function() {
        $(this).focus()
        // If this function exists...
        if (this.setSelectionRange) {
            // ... then use it (Doesn't work in IE)
            // Double the length because Opera is inconsistent about whether a carriage return is one character or two. Sigh.
            var len = index;
            if(len < 0){
                len = $(this).val().length * 2;
            }
            this.setSelectionRange(len, len);
        } else if(this.createTextRange){
            var range = this.createTextRange();
            range.move('character', index);
            range.select();
        }
        else {
            // ... otherwise replace the contents with itself
            // (Doesn't work in Google Chrome)
            $(this).val($(this).val());
        }
        // Scroll to the bottom, in case we're in a tall textarea
        // (Necessary for Firefox and Google Chrome)
        this.scrollTop = 999999;
    });
};

/*! https://mths.be/startswith v0.2.0 by @mathias */
if (!String.prototype.startsWith) {
    (function() {
        'use strict'; // needed to support `apply`/`call` with `undefined`/`null`
        var defineProperty = (function() {
            // IE 8 only supports `Object.defineProperty` on DOM elements
            try {
                var object = {};
                var $defineProperty = Object.defineProperty;
                var result = $defineProperty(object, object, object) && $defineProperty;
            } catch(error) {}
            return result;
        }());
        var toString = {}.toString;
        var startsWith = function(search) {
            if (this == null) {
                throw TypeError();
            }
            var string = String(this);
            if (search && toString.call(search) == '[object RegExp]') {
                throw TypeError();
            }
            var stringLength = string.length;
            var searchString = String(search);
            var searchLength = searchString.length;
            var position = arguments.length > 1 ? arguments[1] : undefined;
            // `ToInteger`
            var pos = position ? Number(position) : 0;
            if (pos != pos) { // better `isNaN`
                pos = 0;
            }
            var start = Math.min(Math.max(pos, 0), stringLength);
            // Avoid the `indexOf` call if no match is possible
            if (searchLength + start > stringLength) {
                return false;
            }
            var index = -1;
            while (++index < searchLength) {
                if (string.charCodeAt(start + index) != searchString.charCodeAt(index)) {
                    return false;
                }
            }
            return true;
        };
        if (defineProperty) {
            defineProperty(String.prototype, 'startsWith', {
                'value': startsWith,
                'configurable': true,
                'writable': true
            });
        } else {
            String.prototype.startsWith = startsWith;
        }
    }());
}

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
    var autocomplete_container = $('#console_autocomplete');

    hljs.highlightBlock(history[0]);

    var command_history = [];
    var history_pointer = -1;

    registerResizeHandler();

    var nametypes = {};
    var autocomplete_options = {};
    var autocomplete_open = false;
    var autocomplete_pointer = -1;

    if(currentNodenet){
        enable();
    }

    bindEvents();

    $(document).on('nodenet_changed', function(event, new_uid){
        currentNodenet = new_uid;
        if(new_uid) enable();
        else disable();
    });

    function enable(){
        input.removeAttr("disabled");
        if($.isEmptyObject(autocomplete_options)){
            getAutocompleteOptions();
        }
    }

    function getAutocompleteOptions(name){
        params = {nodenet_uid: currentNodenet};
        if(name){
            params['name'] = name;
        }
        api.call('get_netapi_signatures', params, function(data){
            if(name){
                var type = data.types[name]
                nametypes[name] = type
                autocomplete_options[type] = data.autocomplete_options[type];
            } else {
                nametypes = data.types;
                autocomplete_options = data.autocomplete_options;
            }
        });

    }

    function disable(){
        input.attr('disabled', 'disabled')
    }

    function isDisabled(){
        return input.attr('disabled');
    }

    function bindEvents(){
        autocomplete_container.on('click', function(event){
            if(isDisabled()) return;
            autocomplete_select(event);
        });
        input.keydown(function(event){
            if(isDisabled()) return;
            var code = input.val();
            switch(event.keyCode){
                case 38: // arrow up
                    if(autocomplete_open){
                        event.preventDefault();
                        autocomplete_prev();
                    } else if(code == '' && history_pointer == -1){
                        event.preventDefault();
                        history_pointer = command_history.length - 1;
                        input.val(command_history[history_pointer])
                        input.putCursorAt(-1)
                    } else if(history_pointer > 0 && code == command_history[history_pointer]) {
                        event.preventDefault();
                        history_pointer -= 1;
                        input.val(command_history[history_pointer])
                        input.putCursorAt(-1)
                    }
                    break;

                case 40: // arrow down
                    if(autocomplete_open){
                        event.preventDefault();
                        autocomplete_next();
                    } else if(history_pointer < command_history.length - 1 && code == command_history[history_pointer]) {
                        event.preventDefault();
                        history_pointer += 1;
                        input.val(command_history[history_pointer])
                        input.putCursorAt(-1)
                    }
                    break;
            }
        });
        input.keyup(function(event){
            if(isDisabled()) return;
            var code = input.val();
            switch(event.keyCode){
                case 13:  // Enter
                    if(autocomplete_open){
                        autocomplete_select(event);
                    } else {
                        if(code.trim().length){
                            submitInput(code);
                        }
                    }
                    break;
                case 32: // spacebar
                    if(event.ctrlKey){
                        autocomplete(true);
                    }
                    break;
                case 27:  // escape
                    stop_autocomplete();
                    break;
                case 38: // arrow up
                case 40: // arrow down
                    // do nothing.
                    break;
                default:
                    history_pointer = -1
                    autocomplete();
            }
        });
        input.blur(function(){
            stop_autocomplete();
        })
    }

    function autocomplete_next(){
        if(autocomplete_pointer < autocomplete_container.children().length - 1){
            autocomplete_pointer += 1;
            $('a.selected', autocomplete_container).removeClass('selected')
            var child = $(autocomplete_container.children()[autocomplete_pointer]);
            $(child.children()).addClass('selected');
            var pos = child.offset().top;

            autocomplete_container.scrollTop(
                autocomplete_container.scrollTop() + child.position().top
                    - autocomplete_container.height()/2 + child.height()/2);
        }
    }

    function autocomplete_prev(){
        if(autocomplete_pointer > 0){
            autocomplete_pointer -= 1;
            $('a.selected', autocomplete_container).removeClass('selected')
            var child = $(autocomplete_container.children()[autocomplete_pointer]);
            $(child.children()).addClass('selected');
            autocomplete_container.scrollTop(
                autocomplete_container.scrollTop() + child.position().top
                    - autocomplete_container.height()/2 + child.height()/2);

        }
    }

    function autocomplete(do_autoselect){
        autocomplete_open = true;
        var code = input.val();
        if(code.indexOf('.') > -1){
            var parts = input.val().split('.');
            var last = parts[parts.length - 1];
            var obj = parts[parts.length - 2];
            obj = obj.match(/([a-zA-Z0-9_]+)/g);
            if(obj)
                obj = obj[obj.length - 1];
            if(!obj || !(obj in nametypes)){
                stop_autocomplete();
            }
            autocomplete_properties(obj, last);
        } else if(code.match(/ ?([a-z0-9]+)?$/m)){
            var parts = input.val().split(' ');
            var last = parts[parts.length - 1];
            autocomplete_names(last);
        }
        if (do_autoselect && autocomplete_container.children().length == 1){
            autocomplete_select();
        }
    }

    function autocomplete_names(start){
        html = [];
        for(var key in nametypes){
            if(start.length == 0 || key.startsWith(start)){
                html.push('<li><a data-complete="name" data="'+key+'">'+key+'</a></li>')
            }
        }
        if(html.length == 0){
            return stop_autocomplete();
        }
        autocomplete_container.html(html.join(''));
        autocomplete_container.css({
            'position': 'absolute',
            'top': input.offset().top + input.height(),
            'left': input.offset().left + (input.val().length * 4),
            'display': 'block'
        });
    }

    function autocomplete_properties(obj, last){
        html = [];
        var type = nametypes[obj];
        var sorted = Object.keys(autocomplete_options[type]).sort();
        for(var i in sorted){
            var key = sorted[i];
            if(key && (last == "" || key.startsWith(last))){
                if(autocomplete_options[type][key] == null){
                    html.push('<li><a data-complete="property" data="'+key+'">'+key+'</a></li>');
                } else {
                    html.push('<li><a data-complete="property" data="'+key+'">'+key+'()</a></li>');
                }
            }
        }
        if (html.length == 0){
            return stop_autocomplete();
        }
        autocomplete_container.html(html.join(''));
        autocomplete_container.css({
            'position': 'absolute',
            'top': input.offset().top + input.height(),
            'left': input.offset().left + (input.val().length * 4),
            'display': 'block'
        });
    }

    function autocomplete_select(event){
        if(event && $(event.target).attr('id') == 'console_input'){
            var el = $('a.selected', autocomplete_container);
            if(el.length == 0){
                var els = $('a', autocomplete_container);
                if(els.length){
                    el = $(els[0]);
                } else {
                    return
                }
            }
        } else {
            if(event){
                var el = $(event.target);
            } else if (autocomplete_container.children().length == 1) {
                var el = $('a', autocomplete_container);
            }
        }
        var val = input.val()
        if(el.attr('data-complete') == 'name'){
            if(val[val.length-1] == " "){
                console.log(val);
                input.val(val + el.attr('data'));
            } else {
                var parts = val.split(" ");
                parts.pop();
                var pre = '';
                if(parts.length){
                    pre = parts.join(" ") +" ";
                }
                input.val(pre + el.attr('data'));
            }
            return stop_autocomplete();
        }
        var selected = el.attr('data');
        var parts = val.split('.');
        var last = null;
        var obj = null;
        if(val.indexOf('.') > -1){
            var last = parts[parts.length - 1];
            var obj = parts[parts.length - 2];
            obj = obj.match(/([a-zA-Z0-9_]+)/g);
            obj = obj[obj.length - 1];
        }
        parts.pop()
        val = parts.join('.') + '.'  + selected;
        var params = [];
        var type = nametypes[obj];
        var data = autocomplete_options[type][selected];
        if(data != null){
            for(var i=0; i < data.length; i++){
                if(!('default' in data[i])){
                    params.push(data[i].name);
                } else {
                    if(data[i].default == null){
                        params.push(data[i].name+'=None')
                    } else if(isNaN(data[i].default)){
                        params.push(data[i].name+'='+'"'+data[i].default+'"')
                    } else {
                        params.push(data[i].name+'='+data[i].default)
                    }
                }
            }
            var length = val.length;
            val += '(' + params.join(', ') + ')';
            input.val(val);
            input.putCursorAt(length + 1);

        } else {
            input.val(val);
            input.putCursorAt(-1);
        }
        stop_autocomplete();
    }

    function stop_autocomplete(){
        autocomplete_open = false;
        autocomplete_pointer = -1;
        autocomplete_container.html('')
        autocomplete_container.hide();
    }

    function submitInput(code){
        api.call('run_netapi_command', {nodenet_uid: currentNodenet, command: code}, function(data){
            getAutocompleteOptions();
            data = data.replace(/\n+/g, '\n')
            var hist = history.text();
            hist += "\n" + code;
            if(data){
                hist += "\n# " + data.replace(/\n/g, "\n# ");
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
                hist += "\n" + code;
                hist += '\n# ERROR: '+error.data.replace(/\n/g, "\n# ");
            }
            history.text(hist);
            input.val('');
            hljs.highlightBlock(history[0]);
            container.scrollTop(999999999)
            command_history.push(code);
        });
    }

});

