const KEY = 'xingyuan.token';
export const session = { get: () => sessionStorage.getItem(KEY), set: v => sessionStorage.setItem(KEY, v), clear: () => sessionStorage.removeItem(KEY) };
export async function api(path, method = 'GET', data) {
  const response = await fetch('/api' + path, {method, headers: {'Content-Type': 'application/json', ...(session.get() ? {Authorization: 'Bearer ' + session.get()} : {})}, ...(data === undefined ? {} : {body: JSON.stringify(data)})});
  const body = await response.json();
  if (!response.ok) {
    if (response.status === 401) { session.clear(); window.dispatchEvent(new Event('session-expired')); }
    throw new Error(typeof body.detail === 'string' ? body.detail : body.detail?.map(x => x.msg).join('；') || '请求失败，请稍后重试');
  }
  return body;
}
