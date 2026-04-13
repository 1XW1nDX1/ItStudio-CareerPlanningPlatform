import React, { useEffect, useRef } from 'react';

const ShaderBackground: React.FC = () => {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        // 保留防止 React 严格模式崩溃的设定
        const gl = canvas.getContext('webgl', { preserveDrawingBuffer: true }) ||
            canvas.getContext('experimental-webgl') as WebGLRenderingContext | null;
        if (!gl) return;

        let animationFrameId: number;

        const vertexShaderSource = `
      attribute vec2 a_position;
      void main() {
        gl_Position = vec4(a_position, 0.0, 1.0);
      }
    `;

        // 核心修复：色彩饱和度回调与抗过曝处理
        const fragmentShaderSource = `
      #ifdef GL_ES
      precision mediump float;
      #endif

      uniform vec2 u_resolution;
      uniform float u_time;

      void main() {
          vec2 uv = gl_FragCoord.xy / u_resolution.xy;
          float t = u_time * 0.4; 

          // 空间扭曲算法：流体推挤
          vec2 p = uv;
          p.x += sin(t * 0.5 + p.y * 3.0) * 0.15;
          p.y += cos(t * 0.3 + p.x * 2.0) * 0.15;

          // 【重调饱和度】：把数值稍微压下来一点点，让粉色和紫色能被肉眼清晰看见，不被白光吃掉
          vec3 color1 = vec3(1.00, 0.78, 0.85); // 明显的暖桃粉色
          vec3 color2 = vec3(1.00, 0.90, 0.65); // 明显的柔和晨金
          vec3 color3 = vec3(0.85, 0.78, 1.00); // 明显的丁香紫

          // 波浪因子
          float wave1 = sin(p.x * 3.0 + t) * 0.5 + 0.5;
          float wave2 = cos(p.y * 2.5 - t * 0.8) * 0.5 + 0.5;

          // 混合三种颜色
          vec3 finalColor = mix(color1, color2, wave1);
          finalColor = mix(finalColor, color3, wave2 * 0.75); // 让紫色的质感透出来
          
          // 删除了导致画面泛白的 highlight 叠加逻辑，保留纯正的色彩质感
          // 整体稍微提亮，保持高级感
          finalColor = finalColor * 1.05;

          gl_FragColor = vec4(finalColor, 1.0);
      }
    `;

        const compileShader = (type: number, source: string) => {
            const shader = gl.createShader(type);
            if (!shader) return null;
            gl.shaderSource(shader, source);
            gl.compileShader(shader);
            return shader;
        };

        const vertexShader = compileShader(gl.VERTEX_SHADER, vertexShaderSource);
        const fragmentShader = compileShader(gl.FRAGMENT_SHADER, fragmentShaderSource);
        if (!vertexShader || !fragmentShader) return;

        const program = gl.createProgram();
        if (!program) return;

        gl.attachShader(program, vertexShader);
        gl.attachShader(program, fragmentShader);
        gl.linkProgram(program);
        gl.useProgram(program);

        const positionBuffer = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
        gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([
            -1.0, -1.0, 1.0, -1.0, -1.0, 1.0,
            -1.0, 1.0, 1.0, -1.0, 1.0, 1.0
        ]), gl.STATIC_DRAW);

        const positionLocation = gl.getAttribLocation(program, 'a_position');
        gl.enableVertexAttribArray(positionLocation);
        gl.vertexAttribPointer(positionLocation, 2, gl.FLOAT, false, 0, 0);

        const resolutionLocation = gl.getUniformLocation(program, 'u_resolution');
        const timeLocation = gl.getUniformLocation(program, 'u_time');

        const render = (time: number) => {
            if (canvas.width !== window.innerWidth || canvas.height !== window.innerHeight) {
                canvas.width = window.innerWidth;
                canvas.height = window.innerHeight;
                gl.viewport(0, 0, canvas.width, canvas.height);
            }
            gl.uniform2f(resolutionLocation, canvas.width, canvas.height);
            gl.uniform1f(timeLocation, time * 0.001);
            gl.drawArrays(gl.TRIANGLES, 0, 6);
            animationFrameId = requestAnimationFrame(render);
        };

        animationFrameId = requestAnimationFrame(render);

        return () => {
            cancelAnimationFrame(animationFrameId);
        };
    }, []);

    return (
        <canvas
            ref={canvasRef}
            style={{ position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh', zIndex: -999, pointerEvents: 'none' }}
        />
    );
};

export default ShaderBackground;