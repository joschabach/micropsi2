
$(function() {

    var dialogs = {

        confirm: function(message, callback){
            $('#confirm_dialog p.message').html(message);
            var el = $('#confirm_dialog');
            var submit = $('#confirm_dialog .btn-confirm');
            el.modal();
            submit.off();
            submit.on('click', function(){
                el.modal('hide');
                callback();
            });
        },

        remote_form_dialog: function(url, callback){
            var el = $('#remote_form_dialog');
            $.ajax(url, {
                success: function(data){
                    // uuh, hacky. but works. :)
                    $('#remote_form_dialog h3').html($('h1', data));
                    $('#remote_form_dialog div.modal-body').html($('form', data));
                    var form = $('#remote_form_dialog form');
                    form.removeClass('span5 span6 span7 span8 span9 span10 span11');
                    $('button', form).hide();
                    $('a.btn', form).hide();
                    var submit = $('#remote_form_dialog .btn-confirm');
                    submit.on('click', function(event){
                        form.ajaxSubmit({
                            success: function(data){
                                el.modal('hide');
                                dialogs.notification('New password saved');
                            },
                            error: function(data){
                                // TODO: error handling
                            }
                        });
                    });
                }
            });
            el.modal();
        },

        notification: function(message){
            $('#notification p.message').html(message);
            var el = $('#notification');
            el.slideDown().delay(2000).fadeOut();
            el.css('left', ($(document.body).width() / 2) - el.width());
        }

    }

    // Bind Menubar links

    // AGENT

    $('.navbar a.agent_delete').on('click', function(){
        dialogs.confirm("Do you really want to delete this blueprint?", function(){
            alert('kthxbye');
        });
    });

    $('.navbar a.agent_save').on('click', function(){
        dialogs.notification("Agent state saved");
    });

    $('.navbar a.agent_revert').on('click', function(){
        dialogs.notification("Agent is being reverted");
    });


    // WORLD
    $('.navbar a.world_delete').on('click', function(){
        dialogs.confirm("Do you really want to delete this world?", function(){
            alert('you bastard');
        });
    });

    $('.navbar a.world_save').on('click', function(){
        dialogs.notification("World state saved");
    });

    $('.navbar a.world_revert').on('click', function(){
        dialogs.notification("World state is being reverted");
    });

    $('a.set_new_password').on('click', function(event){
        event.preventDefault();
        dialogs.remote_form_dialog($(event.target).attr('href'));
    });

});

