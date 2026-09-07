// Original ambient gold shader. Decorative only; CSS remains the fallback.
let dispose = () => {};
export function mountAmbient() {
  dispose();
  const canvas = document.querySelector('[data-ambient]');
  if (!canvas) return;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const gl = canvas.getContext('webgl', {alpha:true, antialias:false, powerPreference:'low-power'});
  if (!gl) return;
  const shaders=[];
  const compile=(type,source)=>{const s=gl.createShader(type);shaders.push(s);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error('Shader unavailable');return s;};
  let program, buffer, frame=0, last=0;
  try {
    program=gl.createProgram();
    gl.attachShader(program,compile(gl.VERTEX_SHADER,'attribute vec2 p; varying vec2 uv; void main(){uv=p*.5+.5;gl_Position=vec4(p,0.,1.);}'));
    gl.attachShader(program,compile(gl.FRAGMENT_SHADER,`precision mediump float;
      varying vec2 uv; uniform float t;
      void main(){ vec2 p=uv; float wave=sin(p.x*5.0+t*.22)*.15+sin(p.x*9.0-t*.13)*.035;
        float d=abs(p.y-.48-wave); float ribbon=exp(-d*15.0); float light=exp(-d*70.0);
        vec3 base=mix(vec3(.95,.91,.80),vec3(.86,.70,.32),p.x*.45);
        vec3 col=mix(base,vec3(1.,.80,.24),ribbon*.65); col+=vec3(.12,.10,.035)*light;
        float grain=fract(sin(dot(p,vec2(12.9898,78.233)))*43758.5453)*.018;
        gl_FragColor=vec4(col-grain,1.); }`));
    gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error('Shader unavailable');
    gl.useProgram(program);buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);
    gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,-1,1,1,-1,1,1]),gl.STATIC_DRAW);
    const position=gl.getAttribLocation(program,'p');gl.enableVertexAttribArray(position);gl.vertexAttribPointer(position,2,gl.FLOAT,false,0,0);
    const time=gl.getUniformLocation(program,'t');
    const draw=(now=0)=>{const rect=canvas.getBoundingClientRect();const ratio=Math.min(devicePixelRatio,1.5);
      const w=Math.max(1,Math.round(rect.width*ratio)),h=Math.max(1,Math.round(rect.height*ratio));
      if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;gl.viewport(0,0,w,h);}
      gl.uniform1f(time,reduced.matches?0:now/1000);gl.drawArrays(gl.TRIANGLES,0,6);};
    const tick=now=>{if(!canvas.isConnected)return;if(now-last>=33){draw(now);last=now;}frame=requestAnimationFrame(tick);};
    const sync=()=>{cancelAnimationFrame(frame);draw();if(!reduced.matches&&!document.hidden)frame=requestAnimationFrame(tick);};
    reduced.addEventListener('change',sync);document.addEventListener('visibilitychange',sync);sync();
    dispose=()=>{cancelAnimationFrame(frame);reduced.removeEventListener('change',sync);document.removeEventListener('visibilitychange',sync);gl.deleteBuffer(buffer);gl.deleteProgram(program);shaders.forEach(s=>gl.deleteShader(s));gl.getExtension('WEBGL_lose_context')?.loseContext();};
  } catch { if(buffer)gl.deleteBuffer(buffer);if(program)gl.deleteProgram(program);shaders.forEach(s=>gl.deleteShader(s)); }
}
