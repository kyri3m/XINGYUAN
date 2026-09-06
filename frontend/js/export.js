import {labels} from './ui.js';

export function tasksCsv(tasks) {
  const rows = [['任务编号','任务名称','企业','状态','地区','开始日期','结束日期','组长','组员'], ...tasks.map(t => [t.pid,t.task_name,t.company,labels[t.status],t.district,t.date_start,t.date_end,t.leader_names,t.member_names])];
  const quote = value => {
    const text = String(value ?? '');
    const safe = /^[\s\u0000-\u001f]*[=+@-]/.test(text) ? "'" + text : text;
    return '"' + safe.replaceAll('"', '""') + '"';
  };
  return '\ufeff' + rows.map(row => row.map(quote).join(',')).join('\r\n');
}
