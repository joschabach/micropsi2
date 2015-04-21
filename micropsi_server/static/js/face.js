var scene, camera, renderer;

var eye_background_color = new THREE.Color(0xFFFFFF);
var pup_color = new THREE.Color(0x523D89);
var nose_color = new THREE.Color(0x694032);
var mouth_color = new THREE.Color(0x764237);

var eye_l_width = 200;
var eye_l_height = 100;
var eye_l_x = -400 + (eye_l_width / 2) + 100 - 2;
var eye_l_y = -400 + (eye_l_height / 2) + 300;
var eye_r_width = 200;
var eye_r_height = 100;
var eye_r_x = -400 + (eye_r_width / 2) + 500 + 2;
var eye_r_y = -400 + (eye_r_height / 2) + 300;

var pup_l_width = 100;
var pup_l_height = 100;
var pup_l_x = -400 + (pup_l_width / 2) + 200;
var pup_l_y = -400 + (pup_l_height / 2) + 300;
var pup_r_width = 100;
var pup_r_height = 100;
var pup_r_x = -400 + (pup_r_width / 2) + 500;
var pup_r_y = -400 + (pup_r_height / 2) + 300;

var nose_width = 200;
var nose_height = 100;
var nose_x = -400 + (nose_width / 2) + 300;
var nose_y = -400 + (nose_height / 2) + 200;

var upper_lip_width = 400;
var upper_lip_height = 45;
var upper_lip_x = -400 + (upper_lip_width / 2) + 200;
var upper_lip_y = -400 + (upper_lip_height / 2) + 145;

var lower_lip_width = 400;
var lower_lip_height = 50;
var lower_lip_x = -400 + (lower_lip_width / 2) + 200;
var lower_lip_y = -400 + (lower_lip_height / 2) + 100;

var corner_l_width = 50;
var corner_l_height = 90;
var corner_l_x = -400 + (corner_l_width / 2) + 200;
var corner_l_y = -400 + (corner_l_height / 2) + 100;

var corner_r_width = 50;
var corner_r_height = 90;
var corner_r_x = -400 + (corner_r_width / 2) + 550;
var corner_r_y = -400 + (corner_r_height / 2) + 100;


var currentNodenet = $.cookie('selected_nodenet') || '';
var emoexpression = {}

var faceVertexShader = [
"varying vec2 vUv;",
"void main() {",
"vUv = uv;",
"gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );",
"}"
].join("\n");

var faceFragmentShader = [
"uniform sampler2D map;",
"uniform vec3 color;",
"varying vec2 vUv;",
"void main() {",
"vec4 texel = texture2D( map, vUv );",
"gl_FragColor = vec4( texel.xyz + color, texel.w );",
"}"
].join("\n")

var file = $("<link>").attr('rel', 'stylesheet').attr('type', 'text/css').attr('href', '/static/css/bootstrap-slider.css');
$("head").append(file);

var id;
$(window).resize(function() {
    clearTimeout(id);
    id = setTimeout(init, 500);
});


init();
register_stepping_function('nodenet', get_nodenet_data, fetchEmoexpressionParameters);

animate();

function init() {

    canvas = document.getElementById("face");
    div = canvas.parentNode;
    canvas.width = div.clientWidth;
    canvas.height = div.clientHeight;

    scene = new THREE.Scene();

    camera = new THREE.PerspectiveCamera( 75, canvas.width / canvas.height, 1, 10000 );
    camera.position.z = 2000;

    texture = THREE.ImageUtils.loadTexture('/static/face/stevehead.png'),
    textureMaterial = new THREE.ShaderMaterial();

    face_background_p = new THREE.PlaneBufferGeometry( 800, 800 )
    face_background_m = new THREE.ShaderMaterial({
        uniforms: {
            map: {type: 't', value: texture},
            color: {type: 'c', value: new THREE.Color( 0x000000 )}
        },
     	vertexShader: faceVertexShader,
        fragmentShader: faceFragmentShader,
        transparent: false
    });

    face_background = new THREE.Mesh( face_background_p, face_background_m );
    scene.add( face_background );

    eye_l_p = new THREE.PlaneBufferGeometry( eye_l_width, eye_l_height );
    eye_l_p.dynamic = true;
    eye_l_m = new THREE.MeshBasicMaterial( { color: eye_background_color, wireframe: false } );
    eye_l = new THREE.Mesh( eye_l_p, eye_l_m );
    eye_l.position.x = eye_l_x;
    eye_l.position.y = eye_l_y;
    scene.add( eye_l );

    eye_r_p = new THREE.PlaneBufferGeometry( eye_r_width, eye_r_height );
    eye_l_p.dynamic = true;
    eye_r_m = new THREE.MeshBasicMaterial( { color: eye_background_color, wireframe: false } );
    eye_r = new THREE.Mesh( eye_r_p, eye_r_m );
    eye_r.position.x = eye_r_x;
    eye_r.position.y = eye_r_y;
    scene.add( eye_r );

    pup_l_p = new THREE.PlaneBufferGeometry( pup_l_width, pup_l_height );
    pup_l_m = new THREE.MeshBasicMaterial( { color: pup_color, wireframe: false } );
    pup_l = new THREE.Mesh( pup_l_p, pup_l_m );
    pup_l.position.x = pup_l_x;
    pup_l.position.y = pup_l_y;
    scene.add( pup_l );

    pup_r_p = new THREE.PlaneBufferGeometry( pup_r_width, pup_r_height );
    pup_r_m = new THREE.MeshBasicMaterial( { color: pup_color, wireframe: false } );
    pup_r = new THREE.Mesh( pup_r_p, pup_r_m );
    pup_r.position.x = pup_r_x;
    pup_r.position.y = pup_r_y;
    scene.add( pup_r );

    nose_p = new THREE.PlaneBufferGeometry( nose_width, nose_height );
    nose_m = new THREE.MeshBasicMaterial( { color: nose_color, wireframe: false } );
    nose = new THREE.Mesh( nose_p, nose_m );
    nose.position.x = nose_x;
    nose.position.y = nose_y;
    scene.add( nose );

    upper_lip_p = new THREE.PlaneBufferGeometry( upper_lip_width, upper_lip_height );
    upper_lip_m = new THREE.MeshBasicMaterial( { color: mouth_color, wireframe: false } );
    upper_lip = new THREE.Mesh( upper_lip_p, upper_lip_m );
    upper_lip.position.x = upper_lip_x;
    upper_lip.position.y = upper_lip_y;
    scene.add( upper_lip );

    lower_lip_p = new THREE.PlaneBufferGeometry(  lower_lip_width,  lower_lip_height );
    lower_lip_m = new THREE.MeshBasicMaterial( { color: mouth_color, wireframe: false } );
    lower_lip = new THREE.Mesh( lower_lip_p, lower_lip_m );
    lower_lip.position.x = lower_lip_x;
    lower_lip.position.y = lower_lip_y;
    scene.add( lower_lip );

    corner_l_p = new THREE.PlaneBufferGeometry(  corner_l_width,  corner_l_height );
    corner_l_m = new THREE.MeshBasicMaterial( { color: mouth_color, wireframe: false } );
    corner_l = new THREE.Mesh( corner_l_p, corner_l_m );
    corner_l.position.x = corner_l_x;
    corner_l.position.y = corner_l_y;
    scene.add( corner_l );

    corner_r_p = new THREE.PlaneBufferGeometry(  corner_r_width,  corner_r_height );
    corner_r_m = new THREE.MeshBasicMaterial( { color: mouth_color, wireframe: false } );
    corner_r = new THREE.Mesh( corner_r_p, corner_r_m );
    corner_r.position.x = corner_r_x;
    corner_r.position.y = corner_r_y;
    scene.add( corner_r );

    renderer = new THREE.WebGLRenderer({canvas: canvas});
    renderer.setSize( canvas.width, canvas.height)

}

function animate() {


    requestAnimationFrame( animate );

    // -- face color

    face_r = 0;
    face_g = 0;
    face_b = 0;

    // activation slightly reddens the face
    face_r += emoexpression["exp_activation"] / 5;

    // anger strongly reddens the face
    face_r += emoexpression["exp_anger"] / 3;
    face_g -= emoexpression["exp_anger"] / 10;
    face_b -= emoexpression["exp_anger"] / 10;

    // fear pales the face
    face_r -= emoexpression["exp_fear"] / 5;
    face_g -= emoexpression["exp_fear"] / 5;
    face_b -= emoexpression["exp_fear"] / 5;

    // pain greens the face
    face_r -= emoexpression["exp_pain"] / 20;
    face_g += emoexpression["exp_pain"] / 20;
    face_b -= emoexpression["exp_pain"] / 20;


    face_background_m.uniforms["color"]["value"] = new THREE.Color(face_r, face_g, face_b );


    // -- pupil position
    pup_depressor = 0
    pup_depressor += emoexpression["exp_sadness"];

    pup_l.position.y = pup_l_y - pup_depressor * 30;
    pup_r.position.y = pup_r_y - pup_depressor * 30;
    pup_l.scale.y = 1-(pup_depressor / 2);
    pup_r.scale.y = 1-(pup_depressor / 2);


    // -- eye height
    eye_l_h = 1;
    eye_r_h = 1;

    // pain lowers eye height left and increases right
    eye_l_h -= emoexpression["exp_pain"] / 2;
    eye_r_h += emoexpression["exp_pain"] / 2;

    // surprise increaes eye height
    eye_l_h += emoexpression["exp_surprise"] * 1.8;
    eye_r_h += emoexpression["exp_surprise"] * 1.8;

    // anger decreases eye height
    eye_l_h -= emoexpression["exp_anger"] / 2;
    eye_r_h -= emoexpression["exp_anger"] / 2;

    // fear increases eye height
    eye_l_h += emoexpression["exp_fear"];
    eye_r_h += emoexpression["exp_fear"];

    eye_l.scale.y = eye_l_h;
    eye_r.scale.y = eye_r_h;


    // -- eye width
    eye_l_w = 1;
    eye_r_w = 1;

    // surprise decreases eye width, slightly
    eye_l_w -= emoexpression["exp_surprise"] / 5;
    eye_r_w -= emoexpression["exp_surprise"] / 5;

    // anger increases eye width
    eye_l_w += emoexpression["exp_anger"] / 2;
    eye_r_w += emoexpression["exp_anger"] / 2;

    // fear increases eye width
    eye_l_w += emoexpression["exp_fear"] / 2;
    eye_r_w += emoexpression["exp_fear"] / 2;

    eye_l.scale.x = eye_l_w;
    eye_r.scale.x = eye_r_w;


    // -- eye position
    eye_raiser = 0

    // surprise increaes eye position
    eye_raiser += emoexpression["exp_surprise"] * 40;

    eye_l.position.y = eye_l_y + eye_raiser;
    eye_r.position.y = eye_r_y + eye_raiser;


    // -- lip corners
    lip_corner_depressor = 0

    // sadness depresses lip corners
    lip_corner_depressor -= emoexpression["exp_sadness"] * 40;

    // joy raises 'em
    lip_corner_depressor += emoexpression["exp_joy"] * 20;

    corner_l.position.y = (corner_l_y + lip_corner_depressor);
    corner_r.position.y = (corner_r_y + lip_corner_depressor);

    // -- lip presser
    lip_presser = 0;

    lip_presser += emoexpression["exp_pain"] * 0.5;
    lip_presser += emoexpression["exp_anger"] * 0.5;
    lip_presser += emoexpression["exp_fear"] * 0.5;
    lip_presser += emoexpression["exp_joy"] * 0.2;

    upper_lip.scale.y = (1-lip_presser);
    lower_lip.scale.y = (1-lip_presser);
    upper_lip.scale.x = (1-(lip_presser / 4));
    lower_lip.scale.x = (1-(lip_presser / 4));
    corner_l.scale.y = (1-lip_presser);
    corner_r.scale.y = (1-lip_presser);
    corner_l.scale.x = (1-lip_presser);
    corner_r.scale.x = (1-lip_presser);

    lower_lip.position.y = lower_lip_y - lip_presser * 20;
    upper_lip.position.y = upper_lip_y - lip_presser * 80;

    corner_l.position.y = corner_l.position.y - lip_presser * 50;
    corner_r.position.y = corner_r.position.y - lip_presser * 50;


    // -- lower lip depressor
    lower_lip_depressor = 0;

    lower_lip_depressor += emoexpression["exp_surprise"] * 50;
    if(lower_lip_depressor > 50) {
        lower_lip_depressor = 50;
    }

    lower_lip.position.y = lower_lip.position.y - lower_lip_depressor;


    renderer.render( scene, camera );

}

var sliders = {};
var inputs = {};

function get_nodenet_data(){
    return {
        'nodespace': "Root",
        'step': 0
    }
}

function fetchEmoexpressionParameters() {
    api.call('get_emoexpression_parameters', {nodenet_uid:currentNodenet}, success=function(data){
        emoexpression = data;
        updateEmoexpressionParameters(data)
    });
}

function updateEmoexpressionParameters(data) {

    var table = $('table.emoexpression');
    if(Object.keys(sliders).length == 0){
        init_sliders(data);
    }

    for(key in data){
        sliders[key].slider('setValue', data[key]);
        inputs[key].val(parseFloat(data[key]).toFixed(2));
    }

}

function init_sliders(data){
    var table = $('table.emoexpression');
    html = '';
    var sorted = [];

    for(key in data){
        sorted.push({'name': key, 'value': data[key]});
    }
    sorted.sort(sortByName);
    // display reversed to get emo_ before base_
    for(var i = sorted.length-1; i >=0; i--){
        html +=
            '<tr>'+
            '<td>'+sorted[i].name+'</td>'+
            '<td><input id="'+sorted[i].name+'" data-target-value="'+sorted[i].name+'" data-slider-id="'+sorted[i].name+'" type="text" data-slider-min="0" data-slider-max="1" data-slider-step="0.01" data-slider-value="'+sorted[i].value+'"/></td>'+
            '<td><input type="text" data-target-value="'+sorted[i].name+'" id="'+sorted[i].name+'_text" class="input-mini" value="'+sorted[i].value+'"/></td>'+
            '</tr>'
    }
    table.html(html);

    $.each(sorted, function(idx, el){
        sliders[el.name] = $('#'+el.name).slider({
            tooltip: 'hide',
            handle: 'triangle'
        }).on('slide', setEmoValue);
        inputs[el.name] = $('#'+el.name+'_text').on('blur', setEmoValue).on('keydown', function(event){
            if(event.keyCode == 13){
                setEmoValue(event);
            } else if(event.keyCode == 38){
                event.target.value = parseFloat(event.target.value) + 0.01;
                setEmoValue(event);
            } else if(event.keyCode == 40){
                event.target.value = parseFloat(event.target.value) - 0.01;
                setEmoValue(event);
            }
        });
    });
}

function setEmoValue(event){
    var key = $(event.target).attr('data-target-value');
    var value;
    if(event.value){
        value = parseFloat(event.value);
    } else {
        value = parseFloat(event.target.value);
    }
    if(value >= 0 && value <= 1){
        emoexpression[key] = value;
    }
    updateEmoexpressionParameters(emoexpression);
    animate();
}
