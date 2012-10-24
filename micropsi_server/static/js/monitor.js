
dialogs.showMonitorGraph = function(event){
    event.preventDefault();
    var link = $(event.target);
    var monitor = monitors[link.attr('data')];
    if(monitor.values.length){
    }
};