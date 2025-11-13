/*
Tarea CG1 - Transformaciones 2D con matrices
Julio César Rodríguez Figueroa
A01029680
 */


'use strict';

import * as twgl from 'twgl-base.js';
import { shapeF } from '../libs/shapes.js';
import { M3 } from '../libs/A01029680_2d-lib.js';
import GUI from 'lil-gui';

// Define the shader code, using GLSL 3.00

const vsGLSL = `#version 300 es
in vec2 a_position;
in vec4 a_color;

uniform vec2 u_resolution;
uniform mat3 u_transforms;

out vec4 v_color;

void main() {
    // Multiply the matrix by the vector, adding 1 to the vector to make
    // it the correct size. Then keep only the two first components
    vec2 position = (u_transforms * vec3(a_position, 1)).xy;

    // Convert the position from pixels to 0.0 - 1.0
    vec2 zeroToOne = position / u_resolution;

    // Convert from 0->1 to 0->2
    vec2 zeroToTwo = zeroToOne * 2.0;

    // Convert from 0->2 to -1->1 (clip space)
    vec2 clipSpace = zeroToTwo - 1.0;

    // Invert Y axis
    //gl_Position = vec4(clipSpace[0], clipSpace[1] * -1.0, 0, 1);
    gl_Position = vec4(clipSpace * vec2(1, -1), 0, 1);
    v_color = a_color;
}
`;

const fsGLSL = `#version 300 es
precision highp float;

in vec4 v_color;

out vec4 outColor;

void main() {
    outColor = v_color;
}
`;


// Structure for the global data of all objects
// Ambos objetos empezarán en el centro del canvas pero se manejaron de forma independiente
const objects = { 
    pivot: { transforms:{ t:{x:550,y:250,z:0}, rr:{x:0,y:0,z:0}, s:{x:1,y:1,z:1} } }, 
    face: { transforms:{ t:{x:550,y:250,z:0}, rr:{x:0,y:0,z:0}, s:{x:1,y:1,z:1} } }, 
}

// Create the data for the vertices of the polyton, as an object with two arrays
// Usada en este caso paraa generar un pivote con n lados
function generateData(sides, centerX, centerY, radius) {
    // The arrays are initially empty
    let arrays =
    {
        // Two components for each position in 2D
        a_position: { numComponents: 2, data: [] },
        // Four components for a color (RGBA)
        a_color:    { numComponents: 4, data: [] },
        // Three components for each triangle, the 3 vertices
        indices:  { numComponents: 3, data: [] }
    };

    // Initialize the center vertex, at the origin and with white color
    arrays.a_position.data.push(centerX);
    arrays.a_position.data.push(centerY);
    arrays.a_color.data.push(1);
    arrays.a_color.data.push(1);
    arrays.a_color.data.push(1);
    arrays.a_color.data.push(1);

    let angleStep = 2 * Math.PI / sides;
    let randomColor = [Math.random(), Math.random(), Math.random(), 1]; // Para generar un color aleatorio para toda la figura
    // Loop over the sides to create the rest of the vertices
    for (let s=0; s<sides; s++) {
        let angle = angleStep * s;
        // Generate the coordinates of the vertex
        let x = centerX + Math.cos(angle) * radius;
        let y = centerY + Math.sin(angle) * radius;
        arrays.a_position.data.push(x);
        arrays.a_position.data.push(y);
        // Generate a random color for all the vertices
        arrays.a_color.data.push(randomColor[0]);
        arrays.a_color.data.push(randomColor[1]);
        arrays.a_color.data.push(randomColor[2]);
        arrays.a_color.data.push(randomColor[3]);
        // Define the triangles, in counter clockwise order
        arrays.indices.data.push(0);
        arrays.indices.data.push(s + 1);
        arrays.indices.data.push(((s + 2) <= sides) ? (s + 2) : 1);
    }
    console.log(arrays);

    return arrays;
}

// Función para generar la forma de la cara

function faceShape(r){
    // Definir los vertices de la cara
    let sides = 18; // Número de lados del polígono que formará la cara
    let rx = 0; // Para asignar una coorndenada X 
    let ry = 0; // Para asignar una coorndenada Y 
    let arrays = generateData(sides, rx, ry, r); // Usar la función para generar un polígono de 12 lados como cara
    // Para añadir los demás atributos como color
    arrays.a_color.data = [];
    let numVertices = arrays.a_position.data.length / 2;
    for (let i = 0; i <= sides; i++) { // Asignar un color a la piel de cada vértice
        arrays.a_color.data.push(0.5); 
        arrays.a_color.data.push(0.3); 
        arrays.a_color.data.push(0.2); 
        arrays.a_color.data.push(1); 
    }

    // Añadir los ojos
    const eyeOffsetX = r / 3;
    const eyeOffsetY = r / 4;
    const eyeSize    = r / 10;

    const leftEyeX  = rx - eyeOffsetX;
    const leftEyeY  = ry - eyeOffsetY;
    const rightEyeX = rx + eyeOffsetX;
    const rightEyeY = ry - eyeOffsetY;

    // Guarda cuántos vértices había antes de añadir ojos
    const base = arrays.a_position.data.length / 2;

    // Ojo izquierdo
    arrays.a_position.data.push(
        leftEyeX - eyeSize, leftEyeY + eyeSize,
        leftEyeX + eyeSize, leftEyeY + eyeSize,
        leftEyeX,           leftEyeY - eyeSize
    );
    arrays.a_color.data.push(0,0,0,1,  0,0,0,1,  0,0,0,1);
    // índices del triángulo izquierdo
    arrays.indices.data.push(base + 0, base + 1, base + 2);

    // Ojo derecho
    arrays.a_position.data.push(
        rightEyeX - eyeSize, rightEyeY + eyeSize,
        rightEyeX + eyeSize, rightEyeY + eyeSize,
        rightEyeX,           rightEyeY - eyeSize
    );
    arrays.a_color.data.push(0,0,0,1,  0,0,0,1,  0,0,0,1);
    // índices del ojo derecho
    arrays.indices.data.push(base + 3, base + 4, base + 5);

    // Añadir la boca
    const mouthOffsetY = r * 0.35; // distancia vertical desde el centro
    const mouthWidth   = r * 0.60; // ancho de la boca
    const mouthHeight  = r * 0.12; // altura de la sonrisa

    const mouthLeftX  = rx - mouthWidth / 2;
    const mouthRightX = rx + mouthWidth / 2;
    const mouthY      = ry + mouthOffsetY;          // debajo del centro
    const mouthTipY   = mouthY + mouthHeight;       // vértice inferior

    // índice base antes de añadir los 3 vértices contando los ojos
    const baseM = arrays.a_position.data.length / 2;

    // Añadimos los 3 vertices de la boca
    arrays.a_position.data.push(
    mouthLeftX,  mouthY,   
    mouthRightX, mouthY,   
    rx,          mouthTipY 
    );

    // color negro para los 3 vértices
    arrays.a_color.data.push(0,0,0,1,  0,0,0,1,  0,0,0,1);

    // índice del triángulo
    arrays.indices.data.push(baseM + 0, baseM + 1, baseM + 2);

    return arrays;
}

// Initialize the WebGL environmnet
function main() {
    const canvas = document.querySelector('canvas');
    const gl = canvas.getContext('webgl2');
    twgl.resizeCanvasToDisplaySize(gl.canvas);
    gl.viewport(0, 0, gl.canvas.width, gl.canvas.height);

    setupUI(gl);

    let sidesPivote = 6; // Número de lados del polígono que formará el pivote

    let rFace = 50; // Radio del círculo que formará la cara
    let rPivote = 25; // Radio del círculo que formará el pivote

    const programInfo = twgl.createProgramInfo(gl, [vsGLSL, fsGLSL]);

    const arrayPivote = generateData(sidesPivote, 0, 0, rPivote);
    const bufferInfo1 = twgl.createBufferInfoFromArrays(gl, arrayPivote);

    const vao1 = twgl.createVAOFromBufferInfo(gl, programInfo, bufferInfo1);

    const arrayFace = faceShape(rFace);

    const bufferInfo2 = twgl.createBufferInfoFromArrays(gl, arrayFace);

    const vao2 = twgl.createVAOFromBufferInfo(gl, programInfo, bufferInfo2);

    render(gl, programInfo, vao1, bufferInfo1, vao2, bufferInfo2);
}

// Function to do the actual display of the objects, en este caso con pivote para la rotación de la cara
function drawScene(gl, vao, programInfo, bufferInfo, tr, pivotTr=null) {

    // Encerramos las transformaciones en una sola matriz desde el inicio
    let transforms = M3.identity();
    transforms = M3.multiply(M3.scale([tr.s.x, tr.s.y]), transforms);

    // Si tenemos pivote, usamos traslación relativa al pivote
    const rel = pivotTr
        ? [tr.t.x - pivotTr.t.x, tr.t.y - pivotTr.t.y]
        : [tr.t.x, tr.t.y];
    transforms = M3.multiply(M3.translation(rel), transforms);

    // 3) Rotación de la cara
    transforms = M3.multiply(M3.rotation(tr.rr.z), transforms);

    // 4) Si hay pivote, por último trasladamos al pivote
    if (pivotTr) {
        transforms = M3.multiply(M3.translation([pivotTr.t.x, pivotTr.t.y]), transforms);
    }

    // Coordenadas propuestas para los uniforms y las transformaciones para todos los objetos de manera inicial
    let uniforms =
    {
        u_resolution: [gl.canvas.width, gl.canvas.height],
        u_transforms: transforms
    }

    gl.useProgram(programInfo.program);

    twgl.setUniforms(programInfo, uniforms);

    gl.bindVertexArray(vao);

    twgl.drawBufferInfo(gl, bufferInfo);
}

// Función que llama el requestAnimationFrame para renderizar continuamente los objetos por separado y poder modificar las transformaciones
function render(gl, programInfo, vao1, bufferInfo1, vao2, bufferInfo2) {
    twgl.resizeCanvasToDisplaySize(gl.canvas);
    gl.viewport(0, 0, gl.canvas.width, gl.canvas.height);
    gl.clear(gl.COLOR_BUFFER_BIT);

    drawScene(gl, vao1, programInfo, bufferInfo1, objects.pivot.transforms); // Dibujar el pivote
    drawScene(gl, vao2, programInfo, bufferInfo2, objects.face.transforms, objects.pivot.transforms); // Dibujar la cara
    
    // Vuelve a llamarse con los argumentos actuales en el siguiente frame
    requestAnimationFrame(() =>
        render(gl, programInfo, vao1, bufferInfo1, vao2, bufferInfo2)
    );
}

function setupUI(gl)
{
    const gui = new GUI();
    // Determinar a las transformaciones del pivote
    const piv = gui.addFolder('Pivot');
    const pT = piv.addFolder('Translation');
    pT.add(objects.pivot.transforms.t, 'x', 0, gl.canvas.width);
    pT.add(objects.pivot.transforms.t, 'y', 0, gl.canvas.height);
    const pS = piv.addFolder('Scale');
    pS.add(objects.pivot.transforms.s, 'x', -5, 5);
    pS.add(objects.pivot.transforms.s, 'y', -5, 5);

    // Determinar a las transformaciones de la cara
    const fac = gui.addFolder('Face');
    const fT = fac.addFolder('Translation');
    fT.add(objects.face.transforms.t, 'x', 0, gl.canvas.width);
    fT.add(objects.face.transforms.t, 'y', 0, gl.canvas.height);
    const fR = fac.addFolder('Rotation');
    fR.add(objects.face.transforms.rr, 'z', 0, Math.PI * 2);
    const fS = fac.addFolder('Scale');
    fS.add(objects.face.transforms.s, 'x', -5, 5);
    fS.add(objects.face.transforms.s, 'y', -5, 5);
}

main()
