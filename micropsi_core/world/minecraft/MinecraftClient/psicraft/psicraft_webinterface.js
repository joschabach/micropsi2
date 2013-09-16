var loaded_blocks = new Array();
var loaded_blocks_symbols = new Array();

paper.install(window);
window.onload = function () {
    paper_scope_bot = new paper.PaperScope();
    botcanvas = document.getElementById('BotCanvas'); // for paper.js
    paper_scope_bot.setup(botcanvas);
    var url = "/static/block_images/bot.png";
    var raster = new paper_scope_bot.Raster(url)
    bot_symbol = new paper_scope_bot.Symbol(raster);

    bot_instance = new paper_scope_bot.PlacedSymbol(bot_symbol);
    bot_instance.position = new paper_scope_bot.Point(20, 20);
    bot_instance.scale(0.1);

    paper_scope_bot.view.draw();

    paper_scope_chunk = new paper.PaperScope();
    chunkcanvas = document.getElementById('ChunkCanvas'); // for paper.js
    paper_scope_chunk.setup(chunkcanvas);

//    paper_scope_bot.view.onFrame = function (event) {
//        // Each frame, rotate the definition
//        // of the symbol by 1 degree:
//        bot_symbol.definition.rotate(1);
//    }
}


function send_command(path) {
    var request = new XMLHttpRequest();
    request.open("GET", path, true);
    request.onreadystatechange = function () {
        if ((request.readyState === 4) && (request.status === 200)) {
            var modify = document.getElementById('log_area');
            modify.innerHTML = request.responseText + "\n" + modify.innerHTML;
        }

    };

    request.send();
}

function redraw_vis() {

    redraw_interval = setInterval(function () {
        query_and_draw()
    }, 1000);

}

function stop_redraw_vis() {

    redraw_interval = window.clearInterval(redraw_interval);

}

function query_and_draw() {

    paper_scope_chunk.project.activeLayer.removeChildren();

    query_and_draw_chunk();
    query_and_draw_bot();

}

function query_and_draw_chunk() {

    var request = new XMLHttpRequest();
    request.open("GET", "http://localhost:8080/query_chunk", true);
    request.onreadystatechange = function () {

        if ((request.readyState === 4) && (request.status === 200)) {

            var blocks_and_botblock_and_layers = JSON.parse(request.responseText);
            var blocks_json = blocks_and_botblock_and_layers[0];
            var bot_block = blocks_and_botblock_and_layers[1];
            var layers = blocks_and_botblock_and_layers[2];
            var answer = blocks_and_botblock_and_layers[3];
            var current_block = 0;
            var canvas_offset = 20 * 16;

            var modify = document.getElementById('log_area');
            modify.innerHTML = answer + ". Now painting chunk ...\n" + modify.innerHTML;


            for (var layer = 0; layer < layers; layer++) {

                for (var rows = 0; rows < 16; rows++) {

                    for (var cols = 15; cols >= 0; cols--) {

                        var block_name = blocks_json[cols][layer][rows];

                        var block_loaded = false;

                        var x_coord = 18 * (cols + rows);
                        var y_coord = canvas_offset + 9 * (rows - cols) - (layer * 20);

                        if (block_name != "0") {


                            if (layer == layers - 1 || rows == 15 || cols == 0) {


                                for (var i = 0; i < loaded_blocks.length; i++) {


                                    if (block_name == loaded_blocks[i]) {

                                        block_loaded = true;
                                        current_block = i;
                                        break;

                                    }

                                    current_block = i + 1;

                                }
                                if (block_loaded == false) {

                                    loaded_blocks[current_block] = block_name;
                                    var url = "/static/block_images/" + block_name + ".png";
                                    var raster = new paper_scope_chunk.Raster(url)
                                    loaded_blocks_symbols[current_block] = new paper_scope_chunk.Symbol(raster);

                                }

                                var instance = new paper_scope_chunk.PlacedSymbol(loaded_blocks_symbols[current_block]);
                                instance.position = new paper_scope_chunk.Point(x_coord, y_coord);
                                instance.scale(0.27);

                            } else if (blocks_json[cols - 1][layer][rows] == "0" ||
                                blocks_json[cols][layer + 1][rows] == "0" ||
                                blocks_json[cols][layer][rows + 1] == "0") {


                                for (var i = 0; i < loaded_blocks.length; i++) {


                                    if (block_name == loaded_blocks[i]) {

                                        block_loaded = true;
                                        current_block = i;
                                        break;

                                    }

                                    current_block = i + 1;

                                }
                                if (block_loaded == false) {

                                    loaded_blocks[current_block] = block_name;
                                    var url = "/static/block_images/" + block_name + ".png";
                                    var raster = new paper_scope_chunk.Raster(url)
                                    loaded_blocks_symbols[current_block] = new paper_scope_chunk.Symbol(raster);

                                }

                                var instance = new paper_scope_chunk.PlacedSymbol(loaded_blocks_symbols[current_block]);
                                instance.position = new paper_scope_chunk.Point(x_coord, y_coord);
                                instance.scale(0.27);

                            }

                        }

                    }

                }

            }

            paper_scope_chunk.view.draw();

            modify.innerHTML = " ... finished painting chunk!\n" + modify.innerHTML;

        }

    };
    request.send();
}

function query_and_draw_bot() {

    var request = new XMLHttpRequest();
    request.open("GET", "http://localhost:8080/query_bot", true);
    request.onreadystatechange = function () {

        if ((request.readyState === 4) && (request.status === 200)) {

            var bot_block_and_layers = JSON.parse(request.responseText);
            var bot_block = bot_block_and_layers[0];
            var layers = bot_block_and_layers[1];
            var answer = bot_block_and_layers[2]
            var canvas_offset = 20 * 16;

            var modify = document.getElementById('log_area');
            modify.innerHTML = answer + ". Now painting Bot ...\n" + modify.innerHTML;

            var img = new Image();

            var x_coord = 18 * (15 + bot_block[0] % 16 + bot_block[2] % 16);
            var y_coord = canvas_offset + 9 * (-15 + bot_block[2] % 16 - bot_block[0] % 16) - ((((layers - 1) / 2) + 2) * 20);

            bot_instance.position = new paper_scope_bot.Point(x_coord, y_coord);
            paper_scope_bot.view.draw();

            modify.innerHTML = " ... finished painting Bot!\n" + modify.innerHTML;

        }

    };
    request.send();
}

function more_layers(path) {

    var request = new XMLHttpRequest();
    request.open("GET", path, true);
    request.onreadystatechange = function () {

        if ((request.readyState === 4) && (request.status === 200)) {
            var modify = document.getElementById('log_area');
            var layers_and_answer = JSON.parse(request.responseText);
            var layers = layers_and_answer[0]
            var answer = layers_and_answer[1]
            modify.innerHTML = answer + "\n" + modify.innerHTML;
            var modify = document.getElementById('layer_div');
            modify.innerHTML = layers + " layers";
        }

    };

    request.send();
}

function fewer_layers(path) {

    var request = new XMLHttpRequest();
    request.open("GET", path, true);
    request.onreadystatechange = function () {

        if ((request.readyState === 4) && (request.status === 200)) {
            console.log("javascript fewer layers - in ready");
            var modify = document.getElementById('log_area');
            var layers_and_answer = JSON.parse(request.responseText);
            console.log("parsed layers: " + layers);
            var layers = layers_and_answer[0]
            var answer = layers_and_answer[1]
            modify.innerHTML = answer + "\n" + modify.innerHTML;
            var modify = document.getElementById('layer_div');
            modify.innerHTML = layers + " layers";
        }

    };

    request.send();
}