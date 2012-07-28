

var dialogs = {

    /**
        renders a simple confirmation modal, containing the given message
        the callback is executed, if the user confirms the dialog.
    */
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


    /**
        renders a modal, with the html obtained from the url.
    */
    remote_form_dialog: function(url, callback){
        $('#remote_form_dialog').html('').modal();
        $.ajax(url, {
            success: function(data){
                dialogs.setModalForm(data, callback);
            }
        });
    },

    /**
        Set the content of the modal and bind form-submit events

        If you want a second dialog, or want to display another dialog,
        use links with the class "modal_followup". The JS will then fetch the html
        from the href attribute, and set it as the dialog's content.

    */
    setModalForm: function(data, callback){
        var el = $('#remote_form_dialog');
        if (data.msg){
            el.modal('hide');
            return dialogs.notification(data.msg, data.status);
        }
        el.html(data);
        var links = $('.modal_followup', el);
        if(links){
            links.on('click', function(event){
                event.preventDefault();
                dialogs.remote_form_dialog($(event.target).attr('href'), callback);
            });
        }
        var submit = $('#remote_form_dialog .btn-primary');
        submit.bind('click', {callback: callback}, dialogs.async_form_submit);
        $('form', el).bind('submit', {callback: callback}, dialogs.async_form_submit);
    },

    /**
        callback after submission of the form.
        The backend can deliver the following responses:

            * A dict, with a 'status' and a 'msg'. The modal will close,
              and the message will be displayed as a notification. the status
              can be one of ['info', 'error', 'success'] to correspond with the
              bootstrap notification themes

            * A dict, with a 'redirect' parameter. The JS will then trigger
              a reload to the given url

            * HTML. The modal will persist, and set the delivered html as its content

    */
    async_form_submit: function(event, callback){
        event.preventDefault();
        var el = $('#remote_form_dialog');
        form = $('form', el);
        form.ajaxSubmit({
            success: function(data){
                if(data.redirect){
                    window.location.replace(data.redirect);
                } else if (data.msg){
                    el.modal('hide');
                    if(data.status == 'success' && event.data.callback){
                        event.data.callback();
                    }
                    dialogs.notification(data.msg, data.status);
                } else {
                    dialogs.setModalForm(data, callback);
                }
            }
        });
    },

    /**
        render a simple and temporary twitter bootstrap notification.
        Parameters:
            message - the message to display
            status - one of ['error', 'info', 'success']
    */
    notification: function(message, status){
        var el = $('#notification');
        $('p.message', el).html(message);
        el.removeClass('alert-info alert-success alert-error');
        if(status != 'error' && status != 'success'){
            status = 'info';
        }
        el.addClass('alert-' + status);
        el.slideDown().delay(2000).fadeOut();
        el.css('left', ($(document.body).width() / 2) - el.width());
    }

};

$(function() {

    // Bind Menubar links

    // NODENET
    function remote_form(event){
        event.preventDefault();
        dialogs.remote_form_dialog($(event.target).attr('href'));
    }

    $('.navbar a.nodenet_new').on('click', remote_form);
    $('.navbar a.nodenet_edit').on('click', remote_form);

    $('.navbar a.nodenet_delete').on('click', function(){
        dialogs.confirm("Do you really want to delete this nodenet?", function(){
            alert('kthxbye');
        });
    });

    $('.navbar a.nodenet_save').on('click', function(){
        dialogs.notification("nodenet state saved");
    });

    $('.navbar a.nodenet_revert').on('click', function(){
        dialogs.notification("nodenet is being reverted");
    });

    $('.navbar a.nodenet_import').on('click', remote_form);
    $('.navbar a.nodenet_merge').on('click', remote_form);


    // WORLD
    $('.navbar a.world_new').on('click', remote_form);
    $('.navbar a.world_edit').on('click', remote_form);

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

    $('.navbar a.world_import').on('click', remote_form);

    // USER

    $('a.set_new_password').on('click', remote_form);

    $('a.create_user').on('click', function(event){
        event.preventDefault();
        dialogs.remote_form_dialog($(event.target).attr('href'), function(){window.location.reload();});
    });

    $('a.login').on('click', function(event){
        event.preventDefault();
        dialogs.remote_form_dialog($(event.target).attr('href'), function(){window.location.reload();});
    });
});


updateWorldAdapterSelector = function() {
    var option = $("#nodenet_world option:selected");
    if (option) {
        $("#nodenet_worldadapter").load("/create_worldadapter_selector/"+option.val());
    }
};

