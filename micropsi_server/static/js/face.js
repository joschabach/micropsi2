var scene, camera, renderer;

var face_base_color = new THREE.Color(0xC69680);
var eye_background_color = new THREE.Color(0xFFFFFF);
var pup_color = new THREE.Color(0x523D89);
var nose_color = new THREE.Color(0x774235);
var mouth_color = new THREE.Color(0x774235);

var eye_l_width = 200;
var eye_l_height = 100;
var eye_l_x = -400 + (eye_l_width / 2) + 100;
var eye_l_y = -400 + (eye_l_height / 2) + 300;
var eye_r_width = 200;
var eye_r_height = 100;
var eye_r_x = -400 + (eye_r_width / 2) + 500;
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

var mouth_width = 400;
var mouth_height = 100;
var mouth_x = -400 + (mouth_width / 2) + 200;
var mouth_y = -400 + (mouth_height / 2) + 100;

var currentNodenet = $.cookie('selected_nodenet') || '';
var emoexpression = {}

init();
register_stepping_function('nodenet', get_nodenet_data, fetch_emoexpression_parameters)

animate();

function init() {

    scene = new THREE.Scene();

    camera = new THREE.PerspectiveCamera( 75, window.innerWidth / window.innerHeight, 1, 10000 );
    camera.position.z = 2000;

    face_background_p = new THREE.PlaneGeometry( 800, 800 )
    face_background_m = new THREE.MeshBasicMaterial( { color: face_base_color, wireframe: false } );
    face_background = new THREE.Mesh( face_background_p, face_background_m );
    scene.add( face_background );

    eye_l_p = new THREE.PlaneGeometry( eye_l_width, eye_l_height )
    eye_l_m = new THREE.MeshBasicMaterial( { color: eye_background_color, wireframe: false } );
    eye_l = new THREE.Mesh( eye_l_p, eye_l_m );
    eye_l.position.x = eye_l_x;
    eye_l.position.y = eye_l_y;
    scene.add( eye_l );

    eye_r_p = new THREE.PlaneGeometry( eye_r_width, eye_r_height )
    eye_r_m = new THREE.MeshBasicMaterial( { color: eye_background_color, wireframe: false } );
    eye_r = new THREE.Mesh( eye_r_p, eye_r_m );
    eye_r.position.x = eye_r_x;
    eye_r.position.y = eye_r_y;
    scene.add( eye_r );

    pup_l_p = new THREE.PlaneGeometry( pup_l_width, pup_l_height )
    pup_l_m = new THREE.MeshBasicMaterial( { color: pup_color, wireframe: false } );
    pup_l = new THREE.Mesh( pup_l_p, pup_l_m );
    pup_l.position.x = pup_l_x;
    pup_l.position.y = pup_l_y;
    scene.add( pup_l );

    pup_r_p = new THREE.PlaneGeometry( pup_r_width, pup_r_height )
    pup_r_m = new THREE.MeshBasicMaterial( { color: pup_color, wireframe: false } );
    pup_r = new THREE.Mesh( pup_r_p, pup_r_m );
    pup_r.position.x = pup_r_x;
    pup_r.position.y = pup_r_y;
    scene.add( pup_r );

    nose_p = new THREE.PlaneGeometry( nose_width, nose_height )
    nose_m = new THREE.MeshBasicMaterial( { color: nose_color, wireframe: false } );
    nose = new THREE.Mesh( nose_p, nose_m );
    nose.position.x = nose_x;
    nose.position.y = nose_y;
    scene.add( nose );

    mouth_p = new THREE.PlaneGeometry( mouth_width, mouth_height )
    mouth_m = new THREE.MeshBasicMaterial( { color: mouth_color, wireframe: false } );
    mouth = new THREE.Mesh( mouth_p, mouth_m );
    mouth.position.x = mouth_x;
    mouth.position.y = mouth_y;
    scene.add( mouth );

    renderer = new THREE.WebGLRenderer();
    renderer.setSize( window.innerWidth, window.innerHeight );

    document.getElementById("facecanvas").appendChild( renderer.domElement );

}

function animate() {

    requestAnimationFrame( animate );

    face_color = face_base_color.clone();
    face_color.r = face_color.r + Math.random();

    //face.material.color = face_color

    renderer.render( scene, camera );

}

function get_nodenet_data(){
    return {
        'nodespace': "Root",
        'step': 0,              // todo: do we need to know the current netstep -1?
        'coordinates': {
            x1: 0,
            x2: 0,
            y1: 0,
            y2: 0
        }
    }
}

function fetch_emoexpression_parameters() {
    api.call('get_emoexpression_parameters', {nodenet_uid:currentNodenet}, success=function(data){
        emoexpression = data;
    });
}