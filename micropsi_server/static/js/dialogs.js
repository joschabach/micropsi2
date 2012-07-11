
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
            $('#remote_form_dialog div.modal-body').html('');
            $.ajax(url, {
                success: function(data){
                    // uuh, hacky. but works. :)
                    $('#remote_form_dialog h3').html($('h1', data));
                    var form = dialogs.patch_form(data);
                    $('#remote_form_dialog div.modal-body').html(form);
                    var submit = $('#remote_form_dialog .btn-confirm');
                    submit.on('click', dialogs.async_form_submit);
                    form.on('submit', dialogs.async_form_submit);
                }
            });
            el.modal();
        },

        patch_form: function(data){
            var form = $('form', data);
            form.removeClass('span5 span6 span7 span8 span9 span10 span11');
            $('button', form).css('visibility', 'hidden');
            $('a.btn', form).hide();
            return form;
        },

        async_form_submit: function(event){
            event.preventDefault();
            var el = $('#remote_form_dialog');
            form.ajaxSubmit({
                success: function(data){
                    if($('.control-group.error', data).length){
                        var form = dialogs.patch_form(data);
                        $('#remote_form_dialog div.modal-body').html(form);
                    } else {
                        el.modal('hide');
                        if(callback){
                            callback();
                        }
                        dialogs.notification('Saved');
                    }
                }
            });
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
    function remote_form(event){
        event.preventDefault();
        dialogs.remote_form_dialog($(event.target).attr('href'));
    }

    $('.navbar a.agent_new').on('click', remote_form);
    $('.navbar a.agent_edit').on('click', remote_form);

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

    $('.navbar a.agent_import').on('click', function(){
        event.preventDefault();
        dialogs.remote_form_dialog($(event.target).attr('href'));
    });

    $('.navbar a.agent_merge').on('click', function(){
        event.preventDefault();
        dialogs.remote_form_dialog($(event.target).attr('href'));
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

    $('.navbar a.world_import').on('click', function(){
        event.preventDefault();
        dialogs.remote_form_dialog($(event.target).attr('href'));
    });

    // USER

    $('a.set_new_password').on('click', function(event){
        event.preventDefault();
        dialogs.remote_form_dialog($(event.target).attr('href'));
    });

    $('a.create_user').on('click', function(event){
        event.preventDefault();
        dialogs.remote_form_dialog($(event.target).attr('href'), function(){window.location.reload();});
    });

});

