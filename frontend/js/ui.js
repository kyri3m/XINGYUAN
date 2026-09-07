export const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const labels = {pending:'待派单',progress:'进行中',done:'已完成',abnormal:'异常',cancelled:'已取消'};
export const badge = status => `<span class="badge ${esc(status)}"><i></i>${labels[status] || esc(status)}</span>`;
export const dateKey = date => `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`;
export const icon = (name, size = 20) => `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${({grid:'<rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/>',tasks:'<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4V2h6v2M9 10h6M9 15h6"/>',calendar:'<rect x="3" y="5" width="18" height="16" rx="3"/><path d="M7 3v4M17 3v4M3 11h18"/>',people:'<circle cx="9" cy="8" r="3"/><path d="M3 21v-3a6 6 0 0112 0v3M17 5a3 3 0 010 6M17 15a5 5 0 014 5"/>',shield:'<path d="M12 3l8 3v6c0 5-8 9-8 9s-8-4-8-9V6zM8 12l3 3 5-6"/>',leaf:'<path d="M20 3C6 1 1 9 6 16s17 3 14-13ZM5 20L16 9"/>',search:'<circle cx="10" cy="10" r="6"/><path d="M15 15l6 6"/>',plus:'<path d="M12 5v14M5 12h14"/>',arrow:'<path d="M5 12h14m-5-5l5 5-5 5"/>',download:'<path d="M12 3v12m-5-5l5 5 5-5M4 16v5h16v-5"/>',logout:'<path d="M9 4H4v16h5M10 12h11m-4-4l4 4-4 4"/>',check:'<path d="M5 12l4 4L19 6"/>',clock:'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',alert:'<path d="M12 3L2 21h20zM12 9v5M12 17v1"/>',chevron:'<path d="M9 5l7 7-7 7"/>',close:'<path d="M6 6l12 12M6 18L18 6"/>',menu:'<path d="M4 6h16M4 12h16M4 18h16"/>'})[name] || '<circle cx="12" cy="12" r="8"/>'}</svg>`;
let timer;
export function toast(message) { const node = document.querySelector('#toast'); node.textContent = message; node.classList.add('show'); clearTimeout(timer); timer = setTimeout(() => node.classList.remove('show'), 3500); }
export function modal(title, content, onSubmit, submitLabel = '保存') {
  const dialog = document.querySelector('#dialog');
  if(dialog.open) dialog.close();
  dialog.innerHTML = `<form id="modal-form"><header><div><h2>${esc(title)}</h2></div><button type="button" class="icon-button" data-close aria-label="关闭">${icon('close')}</button></header><div class="modal-content">${content}</div>${onSubmit ? '<footer><button type="button" class="button" data-close>取消</button><button class="button primary" type="submit">保存</button></footer>' : ''}<p class="form-error" role="alert"></p></form>`;
  dialog.querySelectorAll('[data-close]').forEach(b => b.onclick = () => dialog.close());
  dialog.onclick = e => {if (e.target === dialog) dialog.close();};
  dialog.querySelector('form').onsubmit = async e => {e.preventDefault(); if (!onSubmit) return; const button = e.submitter; button.disabled = true; try {await onSubmit(new FormData(e.target)); dialog.close();} catch(error) {dialog.querySelector('.form-error').textContent = error.message;} finally {button.disabled = false;}};
  if (onSubmit) dialog.querySelector('button[type="submit"]').textContent = submitLabel;
  dialog.showModal();
}
export const field = (name, label, value = '', type = 'text', extra = '') => `<label class="field">${esc(label)}<input name="${name}" type="${type}" value="${esc(value)}" ${extra}></label>`;
export const select = (name, label, options, value = '') => `<label class="field">${esc(label)}<select name="${name}">${options.map(o => {const [v,l] = Array.isArray(o) ? o : [o,o]; return `<option value="${esc(v)}" ${String(v) === String(value) ? 'selected' : ''}>${esc(l)}</option>`;}).join('')}</select></label>`;
export const empty = (message, detail = '添加第一条记录，开始有序协作。') => `<div class="empty">${icon('leaf',32)}<h3>${message}</h3><p>${detail}</p></div>`;
