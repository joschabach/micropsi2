
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


});

