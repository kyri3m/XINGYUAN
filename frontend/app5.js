// Dispatch SPA v5
var TK = localStorage.getItem('tk') || '';
var MU = {};
try { MU = JSON.parse(localStorage.getItem('mu') || '{}'); } catch(e) {}
if (!TK) { location.href = '/login2.html'; }

function hp(k) { if (MU.role === 'admin') return true; return !!(MU.pm || {})[k]; }
function hap() { return hp('admin_panel'); }
function hd() { return { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + TK }; }
async function aj(p, o) {
    o = o || {};
    var r = await fetch(p, { headers: hd(), method: o.m || 'GET', body: o.b || null });
    if (r.status === 401) { localStorage.clear(); location.href = '/login2.html'; return; }
    var d = await r.json();
    if (!r.ok) throw new Error(d.detail || 'fail');
    return d;
}
var pc = []; var mc = null;
async function lr() { if (pc.length) return; try { pc = await aj('/api/personnel'); } catch(e) { pc = []; } }
async function lm() { if (!mc) mc = await aj('/api/meta/permissions'); return mc; }
function $(s) { return document.querySelector(s); }
function $$(s) { return document.querySelectorAll(s); }
function ts(m) { var t = $('#toast'); t.textContent = m; t.classList.add('show'); setTimeout(function() { t.classList.remove('show'); }, 2000); }
function fd(d) { if (!d) return ''; var p = d.split('-'); return parseInt(p[1]) + '/' + parseInt(p[2]); }
function stg(s) { var m = { pending: ['待分配', 'default'], progress: ['进行中', 'info'], done: ['已完成', 'success'], cancelled: ['已取消', 'danger'], abnormal: ['异常', 'danger'] }; var a = m[s] || ['未知', 'default']; return '<span class="tag tag-' + a[1] + '">' + a[0] + '</span>'; }
function pn(s) { if (!s) return ''; return s.split(',').map(function(id) { var p = pc.find(function(x) { return x.id === parseInt(id.trim()); }); return p ? p.name : id; }).join('、'); }
function uru() {
    var ap = hap();
    $$('.nav-item').forEach(function(e) { e.style.display = ap ? '' : 'none'; });
    // worker-only items always visible
    var badge = $('#roleBadge');
    badge.textContent = MU.rl || (ap ? '管理端' : '使用端');
    badge.className = 'role-badge ' + (ap ? 'admin' : 'worker');
    $('#userAvatar').textContent = (MU.dn || '管')[0];
    $('#userName').textContent = MU.dn || '用户';
}
function nav(p) {
    location.hash = '#' + p;
    $$('.nav-item').forEach(function(n) { n.classList.remove('active'); });
    var n = document.querySelector('.nav-item[data-page="' + p + '"]');
    if (n) n.classList.add('active');
    var t = { dashboard: '工作台', tasks: '任务列表', dispatch: '派单计划', personnel: '人员管理', users: '用户管理', mytasks: '我的任务' };
    $('#pageTitle').textContent = t[p] || p;
    rp(p); uru();
}
function lo() { localStorage.clear(); location.href = '/login2.html'; }
function sm(t, b, f) {
    $('#modalBox').innerHTML = '<div class="modal-header"><h3>' + t + '</h3><button class="btn btn-ghost btn-sm" onclick="clm()">✕</button></div><div class="modal-body">' + b + '</div>' + (f ? '<div class="modal-footer">' + f + '</div>' : '');
    $('#modalOverlay').classList.add('show');
}
function clm() { $('#modalOverlay').classList.remove('show'); }
var mo = $('#modalOverlay');
if (mo) mo.addEventListener('click', function(e) { if (e.target === mo) clm(); });

// Dashboard
async function rd() {
    var now = new Date();
    await lhol(now.getFullYear());
    var d = await aj('/api/dashboard');
    var pds = d.periods || {};
    // Period stats
    var ps = '<div class="stats-grid" style="grid-template-columns:repeat(4,1fr)">' +
        statCard('月度待派单', pds.monthly ? pds.monthly.pending : 0, '#1890ff') +
        statCard('季度待派单', pds.quarterly ? pds.quarterly.pending : 0, '#722ed1') +
        statCard('年度待派单', pds.yearly ? pds.yearly.pending : 0, '#eb2f96') +
        statCard('总任务', d.total || 0, '#52c41a') +
        '</div>';
    // Mini calendar
    var miniCal = buildMiniCal(now.getFullYear(), now.getMonth());
    // Today tasks grouped
    var tg = d.today_tasks || {};
    var todayHtml = '';
    Object.keys(tg).forEach(function(ln) {
        var rows = tg[ln].map(function(t) {
            return '<tr style="cursor:pointer" onclick="vt(' + t.id + ')"><td><strong>' + t.pid + '</strong></td><td>' + (t.task_name || '-') + '</td><td>' + (t.valid_period || '-') + '</td><td>' + (t.district || '-') + '</td><td>' + stg(t.status) + '</td></tr>';
        }).join('');
        todayHtml += '<div style="margin-bottom:8px"><strong>👤 ' + ln + '</strong><table style="font-size:11px"><thead><tr><th>编号</th><th>任务名</th><th>有效期</th><th>地区</th><th>状态</th></tr></thead><tbody>' + (rows || '<tr><td colspan="5" style="color:#8c8c8c">无</td></tr>') + '</tbody></table></div>';
    });
    if (!todayHtml) todayHtml = '<p style="color:#8c8c8c;text-align:center;padding:20px">今日无任务</p>';
    // Week tasks per leader
    var wg = d.week_tasks || {};
    var wds = d.week_dates || {};
    var weekHtml = '<div style="margin-bottom:4px;font-size:11px;color:#8c8c8c">📅 ' + (wds.start || '') + ' ~ ' + (wds.end || '') + '</div>';
    var wkeys = Object.keys(wg);
    if (wkeys.length) {
        weekHtml += '<table style="font-size:11px"><thead><tr><th>组长</th><th>未完成</th><th>已完成</th><th>异常</th><th>总计</th></tr></thead><tbody>';
        wkeys.forEach(function(ln) {
            var w = wg[ln];
            weekHtml += '<tr><td><strong>' + ln + '</strong></td><td><span class="tag tag-warning">' + (w.progress || 0) + '</span></td><td><span class="tag tag-success">' + (w.done || 0) + '</span></td><td><span class="tag tag-danger">' + (w.abnormal || 0) + '</span></td><td><b>' + (w.total || 0) + '</b></td></tr>';
        });
        weekHtml += '</tbody></table>';
    } else { weekHtml += '<p style="color:#8c8c8c;text-align:center;padding:10px">本周暂无任务</p>'; }
    // Render
    $('#contentArea').innerHTML =
        ps +
        '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px">' +
        '<div class="panel"><div class="panel-header"><h3>📌 今日任务</h3></div><div class="panel-body">' + todayHtml + '</div></div>' +
        '<div class="panel"><div class="panel-header"><h3>📊 本周任务</h3></div><div class="panel-body">' + weekHtml + '</div></div>' +
        '</div>' +
        '<div class="panel" style="margin-top:12px"><div class="panel-header"><h3>🗓 本月日历</h3></div><div class="panel-body">' + miniCal + '</div></div>';
    $('#headerActions').innerHTML = hp('manage_tasks') ? '<button class="btn btn-primary" onclick="stf()">+ 新建任务</button>' : '';
}
function statCard(l, v, c) { return '<div class="stat-card" style="border-left:3px solid ' + c + '"><div class="val" style="color:' + c + '">' + v + '</div><div class="lbl">' + l + '</div></div>'; }
function buildMiniCal(y, m) {
    var fD = new Date(y, m, 1), lD = new Date(y, m + 1, 0);
    var fs = lds(fD), ls = lds(lD);
    var sm = new Date(fD); sm.setDate(fD.getDate() - fD.getDay());
    if (sm >= fD) sm.setDate(sm.getDate() - 7);
    var da = ['日','一','二','三','四','五','六'];
    var h = '<table style="width:100%;text-align:center;font-size:11px;border-collapse:collapse">';
    h += '<thead><tr>' + da.map(function(x) { return '<th style="padding:4px">' + x + '</th>'; }).join('') + '</tr></thead><tbody>';
    var c = new Date(sm), rows = 0;
    var hy = HOLS[y] || {};
    var today = lds(new Date());
    while (rows < 6 || c <= lD) {
        h += '<tr>';
        for (var d = 0; d < 7; d++) {
            var ds = lds(c);
            var inMonth = ds >= fs && ds <= ls;
            var isToday = ds === today;
            var hi = hy[ds] || null;
            var isHol = hi && hi.holiday === true;
            var isMakeup = hi && hi.holiday === false;
            var dow = c.getDay();
            var isWE = dow === 0 || dow === 6;
            var style = 'padding:4px;';
            if (!inMonth) style += 'color:#d9d9d9;';
            else if (isHol) style += 'color:#ff4d4f;font-weight:bold;';
            else if (isWE) style += 'color:#8c8c8c;';
            if (isToday) style += 'background:#e6f7ff;border-radius:4px;';
            if (isMakeup) style += 'color:#fa8c16;';
            var lbl = c.getDate();
            h += '<td style="' + style + '" title="' + (isHol ? hi.name : isMakeup ? '调休上班' : '') + '">' + lbl + '</td>';
            c.setDate(c.getDate() + 1);
        }
        h += '</tr>';
        rows++;
        if (rows >= 6 && c > lD) break;
    }
    h += '</tbody></table>';
    return h;
}

// Task list
var tft = 'all', tfs = '', tfd = '', tfp = '';
async function rts(f) {
    f = f || 'all'; tft = f;
    await lr();
    var p = f !== 'all' ? '?status=' + f : '';
    if (tfs) p += (p ? '&' : '?') + 'search=' + encodeURIComponent(tfs);
    var tsks = await aj('/api/tasks' + p);
    // Client-side filters
    if (tfd) tsks = tsks.filter(function(t) { return (t.district || '').indexOf(tfd) >= 0; });
    if (tfp) tsks = tsks.filter(function(t) { return t.valid_period === tfp; });
    var fb = ['all', 'pending', 'progress', 'done', 'abnormal', 'cancelled'].map(function(x) {
        var lb = { all: '全部', pending: '待分配', progress: '进行中', done: '已完成', abnormal: '异常', cancelled: '已取消' };
        return '<button class="btn ' + (f === x ? 'btn-primary' : 'btn-ghost') + ' btn-sm" onclick="rts(\'' + x + '\')">' + (lb[x] || x) + '</button>';
    }).join('');
    var cm = hp('manage_tasks');
    var lp = pc.find(function(x) { return x.user_id === MU.id; });
    // Build district filter options
    var distFilterOpts = '<option value="">全部地区</option>';
    Object.keys(AH_DISTRICTS).forEach(function(c) { distFilterOpts += '<option value="' + c + '"' + (tfd === c ? ' selected' : '') + '>' + c + '</option>'; });
    var periodOpts = ['月度','季度','半年度','年度','月度+季度','月度+半年度','季度+半年度','月度+季度+半年度'];
    var periodFilterOpts = '<option value="">全部有效期</option>';
    periodOpts.forEach(function(v) { periodFilterOpts += '<option value="' + v + '"' + (tfp === v ? ' selected' : '') + '>' + v + '</option>'; });
    var h = '<div style="display:flex;gap:6px;margin-bottom:10px;align-items:center;flex-wrap:wrap">' + fb;
    h += '<select id="tf_dist_f" onchange="tfd=this.value;rts(tft)" style="padding:4px 8px;border:1px solid #e8e8e8;border-radius:4px;font-size:12px">' + distFilterOpts + '</select>';
    h += '<select id="tf_per_f" onchange="tfp=this.value;rts(tft)" style="padding:4px 8px;border:1px solid #e8e8e8;border-radius:4px;font-size:12px">' + periodFilterOpts + '</select>';
    h += '<div class="search-box" style="margin-left:auto"><input type="text" id="st" placeholder="🔍 搜索... " value="' + tfs + '" onkeyup="if(event.key===\'Enter\'){tfs=this.value;rts(tft)}"><button class="btn btn-sm" onclick="tfs=$(\'#st\').value;rts(tft)">搜索</button>' + (tfs || tfd || tfp ? '<button class="btn btn-sm btn-ghost" onclick="tfs=\'\';tfd=\'\';tfp=\'\';rts(tft)">清除</button>' : '') + '</div>';
    if (cm) h += '<button class="btn btn-primary btn-sm" onclick="stf()">+ 新建任务</button>';
    h += '</div><div class="panel"><div class="panel-body"><table><thead><tr><th>编号</th><th>任务名</th><th>类别</th><th>有效期</th><th>地区</th><th>检测</th><th>日期</th><th>组长</th><th>状态</th><th>操作</th></tr></thead><tbody>';
    tsks.forEach(function(t) {
        var ops = ['<button class="btn btn-sm btn-ghost" onclick="vt(' + t.id + ')">查看</button>'];
        if (cm) { ops.push('<button class="btn btn-sm" onclick="etf(' + t.id + ')">编辑</button>', '<button class="btn btn-sm btn-danger" onclick="dlt(' + t.id + ')">删除</button>'); }
        var imt = lp && String(lp.id) === t.leader_ids;
        if (lp && t.status === 'progress' && imt) { ops.push('<button class="btn btn-sm btn-success" onclick="lct(' + t.id + ')">完成</button>', '<button class="btn btn-sm btn-danger" onclick="lat(' + t.id + ')">异常</button>'); }
        if ((cm || (lp && imt)) && t.status !== 'cancelled' && t.status !== 'done' && t.status !== 'abnormal') ops.push('<button class="btn btn-sm btn-danger" onclick="lcl(' + t.id + ')">取消</button>');
        var ti = (t.testing_items || []).map(function(c) { return '<span class="tag tag-default">' + c.category + ':' + c.items.length + '项</span>'; }).join('') || '-';
        h += '<tr style="cursor:pointer" onclick="vt(' + t.id + ')"><td><strong>' + t.pid + '</strong></td><td>' + (t.task_name || '-') + '</td><td>' + (t.project_type || '-') + '</td><td>' + (t.valid_period || '-') + '</td><td>' + (t.district || '-') + '</td><td>' + ti + '</td><td>' + (t.date_start ? fd(t.date_start) + '~' + fd(t.date_end) : '<span class="tag tag-warning">未派单</span>') + '</td><td>' + (t.leader_names || '-') + '</td><td>' + stg(t.status) + (t.cancel_reason ? '<br><small style="color:#ff4d4f">' + t.cancel_reason + '</small>' : '') + '</td><td>' + ops.join(' ') + '</td></tr>';
    });
    h += '</tbody></table></div></div>';
    $('#contentArea').innerHTML = h;
    $('#headerActions').innerHTML = '';
}
async function lct(id) { var h = parseFloat(prompt('实际用时(h):', '')); var b = { status: 'done' }; if (h) b.actual_hrs = h; try { await aj('/api/tasks/' + id, { m: 'PUT', b: JSON.stringify(b) }); rts(tft); ts('🎉 已完成'); } catch (e) { ts('❌ ' + e.message); } }
async function lat(id) { var r = prompt('异常原因:', ''); if (!r) { ts('必须填写原因'); return; } try { await aj('/api/tasks/' + id, { m: 'PUT', b: JSON.stringify({ status: 'abnormal', cancel_reason: r }) }); rts(tft); ts('⚠️ 异常'); } catch (e) { ts('❌ ' + e.message); } }
async function lcl(id) { var r = prompt('取消原因:', ''); if (!r) { ts('必须填写原因'); return; } try { await aj('/api/tasks/' + id, { m: 'PUT', b: JSON.stringify({ status: 'cancelled', cancel_reason: r }) }); rts(tft); ts('🚫 已取消'); } catch (e) { ts('❌ ' + e.message); } }

function tir() { return '<div class="ti-row" style="display:flex;gap:4px;align-items:center;margin:3px 0"><input class="ti-point" placeholder="点位" style="width:80px;padding:3px 5px;border:1px solid #e8e8e8;border-radius:3px;font-size:11px"><input class="ti-factor" placeholder="因子" style="width:80px;padding:3px 5px;border:1px solid #e8e8e8;border-radius:3px;font-size:11px"><input class="ti-freq" placeholder="频次" style="width:60px;padding:3px 5px;border:1px solid #e8e8e8;border-radius:3px;font-size:11px"><input class="ti-note" placeholder="备注" style="flex:1;padding:3px 5px;border:1px solid #e8e8e8;border-radius:3px;font-size:11px"><button class="btn btn-sm btn-danger" onclick="this.parentElement.remove()">✕</button></div>'; }
var AH_DISTRICTS = { '合肥市': ['瑶海区','庐阳区','蜀山区','包河区','长丰县','肥东县','肥西县','庐江县','巢湖市'], '芜湖市': ['镜湖区','弋江区','鸠江区','三山区','湾沚区','繁昌区','南陵县','无为市'], '蚌埠市': ['龙子湖区','蚌山区','禹会区','淮上区','怀远县','五河县','固镇县'], '淮南市': ['大通区','田家庵区','谢家集区','八公山区','潘集区','凤台县','寿县'], '马鞍山市': ['花山区','雨山区','博望区','当涂县','含山县','和县'], '淮北市': ['杜集区','相山区','烈山区','濉溪县'], '铜陵市': ['铜官区','义安区','郊区','枞阳县'], '安庆市': ['迎江区','大观区','宜秀区','桐城市','怀宁县','潜山市','太湖县','宿松县','望江县','岳西县'], '黄山市': ['屯溪区','黄山区','徽州区','歙县','休宁县','黟县','祁门县'], '滁州市': ['琅琊区','南谯区','天长市','明光市','来安县','全椒县','定远县','凤阳县'], '阜阳市': ['颍州区','颍东区','颍泉区','界首市','临泉县','太和县','阜南县','颍上县'], '宿州市': ['埇桥区','砀山县','萧县','灵璧县','泗县'], '六安市': ['金安区','裕安区','叶集区','霍邱县','舒城县','金寨县','霍山县'], '亳州市': ['谯城区','涡阳县','蒙城县','利辛县'], '池州市': ['贵池区','东至县','石台县','青阳县'], '宣城市': ['宣州区','宁国市','广德市','郎溪县','泾县','绩溪县','旌德县'] };
function buildCityOpts() { var o = '<option value="">— 选择市 —</option>'; Object.keys(AH_DISTRICTS).forEach(function(c) { o += '<option value="' + c + '">' + c + '</option>'; }); return o; }
function buildDistOpts(city) { var o = '<option value="">— 选择区县 —</option>'; if (city && AH_DISTRICTS[city]) AH_DISTRICTS[city].forEach(function(d) { o += '<option value="' + d + '">' + d + '</option>'; }); return o; }
function onCityChange(v) { var sel = document.getElementById('tf_district'); sel.innerHTML = buildDistOpts(v); }

function stf(id) {
    var cats = [
        { k: '有组织', l: '🏭 有组织排放', h: true },
        { k: '无组织', l: '🌫 无组织排放', h: true },
        { k: '废雨水', l: '💧 废（雨）水', h: true },
        { k: '地下水', l: '💧 地下水', h: true },
        { k: '噪声', l: '🔊 噪声', h: false },
        { k: '土壤', l: '🪨 土壤', h: true }
    ];
    var cs = '';
    cats.forEach(function(c, i) {
        cs += '<div style="margin-bottom:8px;border:1px solid #e8e8e8;border-radius:6px;padding:8px"><div style="display:flex;justify-content:space-between"><strong style="font-size:12px">' + c.l + '</strong>' + (c.h ? '<button class="btn btn-sm btn-ghost" onclick="ati(' + i + ')">+</button>' : '') + '</div><div class="tc-' + i + '"></div></div>';
    });
    var distOpts = '';
    sm(id ? '编辑任务' : '新建任务',
        '<input type="hidden" id="tf_id" value="' + (id || '') + '">' +
        '<div class="form-row"><div class="form-group"><label>项目编号 *</label><input id="tf_pid"></div><div class="form-group"><label>任务名称</label><input id="tf_tname"></div></div>' +
        '<div class="form-row"><div class="form-group"><label>项目类别</label><select id="tf_ptype" onchange="onPtypeChange(this.value)"><option value="">— 选择 —</option><option value="自行检测">自行检测</option><option value="委托检测">委托检测</option><option value="比对监测">比对监测</option><option value="验收检测">验收检测</option></select></div><div class="form-group"><label>有效期</label><select id="tf_period"><option value="">— 选择 —</option><option value="月度">月度</option><option value="季度">季度</option><option value="半年度">半年度</option><option value="年度">年度</option><option value="月度+季度">月度+季度</option><option value="月度+半年度">月度+半年度</option><option value="季度+半年度">季度+半年度</option><option value="月度+季度+半年度">月度+季度+半年度</option></select></div></div>' +
        '<div class="form-row"><div class="form-group"><label>项目联系人</label><input id="tf_contact"></div><div class="form-group"><label>联系方式</label><input id="tf_phone"></div></div>' +
        '<div class="form-row"><div class="form-group"><label>市场经理</label><input id="tf_manager"></div><div class="form-group"></div></div>' +
        '<div class="form-row"><div class="form-group"><label>市</label><select id="tf_city" onchange="onCityChange(this.value)">' + buildCityOpts() + '</select></div><div class="form-group"><label>区县</label><select id="tf_district">' + buildDistOpts() + '</select></div></div>' +
        '<div class="form-row"><div class="form-group"><label>计划时长(h)</label><input type="number" id="tf_hrs" step="0.5"></div><div class="form-group"></div></div>' +
        '<strong style="font-size:12px">📋 待检测</strong>' + cs +
        '<div class="form-group"><label>备注</label><textarea id="tf_note" rows="2"></textarea></div>',
        '<button class="btn" onclick="clm()">取消</button><button class="btn btn-primary" onclick="svt()">保存</button>');
    if (id) aj('/api/tasks').then(function(tsks) { var t = tsks.find(function(x) { return x.id === id; }); if (t) { $('#tf_pid').value = t.pid; $('#tf_tname').value = t.task_name || ''; $('#tf_ptype').value = t.project_type || ''; $('#tf_period').value = t.valid_period || ''; $('#tf_contact').value = t.contact_person || ''; $('#tf_phone').value = t.contact_phone || ''; $('#tf_manager').value = t.market_manager || ''; $('#tf_hrs').value = t.planned_hrs || ''; $('#tf_note').value = t.note || ''; var d = (t.district || '').trim(); var city = '', dist = ''; if (d.indexOf(' ') > 0) { var p = d.split(' '); city = p[0]; dist = p.slice(1).join(' '); } $('#tf_city').value = city; onCityChange(city); setTimeout(function() { $('#tf_district').value = dist; }, 50); (t.testing_items || []).forEach(function(cat, i) { (cat.items || []).forEach(function(item) { ati(i, item); }); }); } });
}
function ati(n, pf) { var c = document.querySelector('.tc-' + n); if (!c) return; var d = document.createElement('div'); d.innerHTML = tir(); var r = d.firstElementChild; if (pf) { r.querySelector('.ti-point').value = pf.point || ''; r.querySelector('.ti-factor').value = pf.factor || ''; r.querySelector('.ti-freq').value = pf.frequency || pf.freq || ''; r.querySelector('.ti-note').value = pf.note || ''; } c.appendChild(r); }
async function svt() {
    var id = $('#tf_id').value;
    var cats = ['有组织', '无组织', '废雨水', '地下水', '噪声', '土壤'];
    var ti = cats.map(function(cat, i) {
        var rs = document.querySelectorAll('.tc-' + i + ' > div');
        var items = [];
        rs.forEach(function(r) {
            var pt = r.querySelector('.ti-point').value.trim();
            var fc = r.querySelector('.ti-factor').value.trim();
            var fq = r.querySelector('.ti-freq').value.trim();
            var nt = r.querySelector('.ti-note').value.trim();
            if (pt || fc || fq) items.push({ point: pt, factor: fc, frequency: fq, note: nt });
        });
        return { category: cat, items: items };
    });
    var d = { pid: $('#tf_pid').value, task_name: $('#tf_tname').value, company: '', planned_hrs: parseFloat($('#tf_hrs').value) || 0, testing_items: ti, project_type: $('#tf_ptype').value, valid_period: $('#tf_period').value, contact_person: $('#tf_contact').value, contact_phone: $('#tf_phone').value, project_region: '', market_manager: $('#tf_manager').value, district: ($('#tf_city').value + ' ' + $('#tf_district').value).trim(), note: $('#tf_note').value, status: 'pending' };
    if (!d.pid) { ts('请填写项目编号'); return; }
    try { if (id) { await aj('/api/tasks/' + id, { m: 'PUT', b: JSON.stringify(d) }); } else { await aj('/api/tasks', { m: 'POST', b: JSON.stringify(d) }); } clm(); rts(tft); ts('✅ 已保存'); } catch (e) { ts('❌ ' + e.message); }
}
function onPtypeChange(v) { if (v === '比对监测') $('#tf_period').value = '季度'; }
function etf(id) { stf(id); }
async function dlt(id) { if (!confirm('确认删除？')) return; await aj('/api/tasks/' + id, { m: 'DELETE' }); rts(tft); ts('🗑️ 已删除'); }

// Task detail
async function vt(id) {
    await lr();
    var tsks = await aj('/api/tasks');
    var t = tsks.find(function(x) { return x.id === id; });
    if (!t) { ts('不存在'); return; }
    var ih = '';
    (t.testing_items || []).forEach(function(cat) {
        var rs = '';
        (cat.items || []).forEach(function(item) { rs += '<tr><td>' + (item.point || '-') + '</td><td>' + (item.factor || '-') + '</td><td>' + (item.frequency || item.freq || '-') + '</td><td>' + (item.note || '-') + '</td></tr>'; });
        if (rs) ih += '<div style="margin-bottom:8px"><strong>' + cat.category + '</strong><table><thead><tr><th>点位</th><th>因子</th><th>频次</th><th>备注</th></tr></thead><tbody>' + rs + '</tbody></table></div>';
    });
    if (!ih) ih = '<p style="color:#8c8c8c">无检测项目</p>';
    var ft = [];
    if (hp('manage_tasks')) ft.push('<button class="btn btn-primary" onclick="clm();etf(' + t.id + ')">编辑</button>');
    ft.push('<button class="btn" onclick="clm()">关闭</button>');
    sm('📋 ' + t.pid,
        '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:13px;margin-bottom:12px"><div><strong>任务名称：</strong>' + (t.task_name || '-') + '</div><div><strong>项目类别：</strong>' + (t.project_type || '-') + '</div><div><strong>有效期：</strong>' + (t.valid_period || '-') + '</div><div><strong>项目联系人：</strong>' + (t.contact_person || '-') + '</div><div><strong>联系方式：</strong>' + (t.contact_phone || '-') + '</div><div><strong>市场经理：</strong>' + (t.market_manager || '-') + '</div><div><strong>地区：</strong>' + (t.district || '-') + '</div><div><strong>状态：</strong>' + stg(t.status) + '</div><div><strong>时长：</strong>' + t.planned_hrs + 'h' + (t.actual_hrs ? ' / 实际' + t.actual_hrs + 'h' : '') + '</div><div><strong>日期：</strong>' + (t.date_start ? t.date_start + ' ~ ' + t.date_end : '未派单') + '</div><div><strong>组长：</strong>' + (t.leader_names || '-') + '</div><div><strong>组员：</strong>' + (t.member_names || '-') + '</div><div><strong>备注：</strong>' + (t.note || '-') + '</div></div>' + (t.cancel_reason ? '<div style="background:#fff2e8;padding:8px;border-radius:6px;margin-bottom:12px"><strong>' + (t.status === 'abnormal' ? '⚠️ 异常' : '🚫 取消') + '原因：</strong>' + t.cancel_reason + '</div>' : '') + '<strong>📋 检测项目</strong><div>' + ih + '</div>',
        ft.join(' ')
    );
}

// Dispatch
var dy, dm, dw;
var HOLS = {}; // { '2026-01-01': '元旦', '2026-05-01': '劳动节', ... }
async function lhol(y) { if (HOLS[y]) return; try { var r = await fetch('https://timor.tech/api/holiday/year/' + y); var j = await r.json(); if (j.code === 0) { HOLS[y] = {}; Object.keys(j.holiday).forEach(function(k) { HOLS[y][y + '-' + k] = j.holiday[k]; }); } } catch(e) { HOLS[y] = {}; } }
function lds(d) { return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); }
async function rds() { await lr(); var td = new Date(); dy = td.getFullYear(); dm = td.getMonth(); bm(dy, dm); }
async function bm(y, m) {
    dy = y; dm = m;
    await lhol(dy);
    var hy = HOLS[dy] || {};
    var fD = new Date(y, m, 1), lD = new Date(y, m + 1, 0);
    var fs = y + '-' + String(m + 1).padStart(2, '0') + '-01';
    var ls = y + '-' + String(m + 1).padStart(2, '0') + '-' + String(lD.getDate()).padStart(2, '0');
    var sm = new Date(fD); sm.setDate(fD.getDate() - fD.getDay() + 1);
    if (sm < fD) sm = new Date(fD);
    var wks = [], c = new Date(sm), wn = 0;
    while (c <= lD) {
        var days = [];
        for (var d = 0; d < 7; d++) { var day = new Date(c); day.setDate(c.getDate() + d); var ds = lds(day); if (ds >= fs && ds <= ls) days.push(ds); }
        if (days.length > 0) {
            var wd = days.filter(function(d) {
                var hi = hy[d];
                if (hi && hi.holiday === true) return false;  // real holiday -> not workday
                if (hi && hi.holiday === false) return true;   // makeup workday -> is workday
                var dow = new Date(d + 'T00:00:00').getDay();
                return dow >= 1 && dow <= 5;  // normal weekday
            }).length;
            wks.push({ label: '第' + (wn + 1) + '周 ' + fd(days[0]) + '~' + fd(days[days.length - 1]), sub: wd + '个工作日', days: days }); wn++;
        }
        c.setDate(c.getDate() + 7);
    }
    dw = wks;
    var today = new Date().toISOString().slice(0, 10);
    var cw = 0;
    wks.forEach(function(w, i) { if (w.days.indexOf(today) >= 0) cw = i; });
    rdw(cw);
}
function ms() {
    var mn = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'], bt = '';
    for (var i = 0; i < 12; i++) bt += '<button class="btn ' + (i === dm ? 'btn-primary' : 'btn-ghost') + ' btn-sm" onclick="bm(' + dy + ',' + i + ')">' + mn[i] + '</button>';
    return '<div style="display:flex;gap:4px;align-items:center;flex-wrap:wrap;margin-bottom:10px"><button class="btn btn-sm" onclick="bm(' + (dy - 1) + ',' + dm + ')">◀◀ ' + (dy - 1) + '</button><strong>' + dy + '</strong><button class="btn btn-sm" onclick="bm(' + (dy + 1) + ',' + dm + ')">' + (dy + 1) + ' ▶▶</button><span style="margin:0 8px;color:#e8e8e8">|</span>' + bt + '</div>';
}
async function rdw(wi) {
    await lr();
    await lhol(dy);
    var week = dw[wi];
    var tsks = (await aj('/api/tasks')).filter(function(t) { return t.date_start && t.date_end && t.date_start <= week.days[week.days.length - 1] && t.date_end >= week.days[0]; });
    var lm = {}, lo = [];
    tsks.forEach(function(t) { var ids = (t.leader_ids || '').split(',').map(function(s) { return s.trim(); }).filter(Boolean); ids.forEach(function(lid) { if (!lm[lid]) { lm[lid] = { id: lid, name: pn(lid), days: {} }; lo.push(lid); } week.days.forEach(function(d) { if (t.date_start <= d && t.date_end >= d) { if (!lm[lid].days[d]) lm[lid].days[d] = []; lm[lid].days[d].push(t); } }); }); });
    var da = ['日', '一', '二', '三', '四', '五', '六'];
    var hy = HOLS[dy] || {};
    var dh = week.days.map(function(d) { var dt = new Date(d + 'T00:00:00'); var we = dt.getDay() === 0 || dt.getDay() === 6; var hi = hy[d] || null; var isHol = hi && hi.holiday; var holStyle = isHol ? 'color:#ff4d4f;font-weight:bold;' : ''; var weStyle = we && !isHol ? 'color:#8c8c8c;background:#fafafa;' : ''; var lbl = isHol ? hi.name : da[dt.getDay()]; return '<th style="text-align:center;min-width:50px;font-size:10px;' + weStyle + holStyle + '">' + fd(d) + '<br><small>' + lbl + '</small></th>'; }).join('');
    var lr2 = '';
    lo.forEach(function(lid) { var l = lm[lid]; var cells = ''; week.days.forEach(function(d) { var dt = l.days[d] || []; cells += '<td style="vertical-align:top;padding:1px;font-size:9px">' + dt.map(function(t) { var cls = t.status === 'done' ? 'done' : t.status === 'progress' ? 'progress' : ''; return '<div class="task-card ' + cls + '" onclick="event.stopPropagation();dpt(' + t.id + ')" title="' + t.pid + ' ' + (t.task_name || '') + '" style="padding:2px 3px;font-size:9px;cursor:pointer">' + t.pid.slice(-6) + '</div>'; }).join('') + '</td>'; }); lr2 += '<tr><td style="font-weight:600;font-size:11px;background:#fafafa;position:sticky;left:0">👤 ' + l.name + '</td>' + cells + '</tr>'; });
    if (!lo.length) lr2 = '<tr><td colspan="100" style="text-align:center;color:#8c8c8c;padding:40px">本周暂无派单</td></tr>';
    var wp = tsks.filter(function(t) { return t.status === 'pending'; }).length;
    var wg = tsks.filter(function(t) { return t.status === 'progress'; }).length;
    var wb = dw.map(function(w, i) { return '<button class="btn ' + (i === wi ? 'btn-primary' : 'btn-ghost') + ' btn-sm" onclick="rdw(' + i + ')">' + w.label + '<br><small>' + w.sub + '</small></button>'; }).join('');
    var td2 = 0, wd2 = 0, hd2 = 0;
    for (var d = 1; d <= new Date(dy, dm + 1, 0).getDate(); d++) { var ds2 = dy + '-' + String(dm + 1).padStart(2, '0') + '-' + String(d).padStart(2, '0'); var day2 = new Date(ds2 + 'T00:00:00'); var dow2 = day2.getDay(); td2++; if (hy[ds2] && hy[ds2].holiday === true) { hd2++; } else if (hy[ds2] && hy[ds2].holiday === false) { wd2++; } else if (dow2 >= 1 && dow2 <= 5) { wd2++; } }
    var holDays = Object.entries(hy).filter(function(e) { var dd = new Date(e[0]); return dd.getMonth() === dm && dd.getFullYear() === dy && e[1].holiday; }).sort(function(a,b) { return a[0].localeCompare(b[0]); });
    // Group consecutive dates with same name into ranges
    var hnames = '', grp = null;
    holDays.forEach(function(e) {
        var d = new Date(e[0]);
        var day = d.getDate();
        var nm = e[1].name;
        if (grp && grp.name === nm && grp.end === day - 1) { grp.end = day; }
        else { if (grp) { hnames += (hnames ? '，' : '') + (grp.start === grp.end ? (dm+1)+'月'+grp.start+'日' : (dm+1)+'月'+grp.start+'-'+grp.end+'日') + ' ' + grp.name; } grp = { name: nm, start: day, end: day }; }
    });
    if (grp) { hnames += (hnames ? '，' : '') + (grp.start === grp.end ? (dm+1)+'月'+grp.start+'日' : (dm+1)+'月'+grp.start+'-'+grp.end+'日') + ' ' + grp.name; }
    var wstats = '<div style="display:flex;gap:12px;padding:8px 12px;background:#f6f8fa;border-radius:6px;font-size:12px;flex-wrap:wrap">' + '<span>📅 本月 <b>' + td2 + '</b> 天</span>' + '<span style="color:#52c41a">✅ 工作日 <b>' + wd2 + '</b></span>' + '<span style="color:#8c8c8c">💤 周末 <b>' + (td2 - wd2 - hd2) + '</b></span>' + (hd2 > 0 ? '<span style="color:#ff4d4f">🎌 节假日 <b>' + hd2 + '</b> (' + hnames + ')</span>' : '') + '</div>';
    var re = $('#contentArea').innerHTML = ms() + '<div style="display:flex;gap:4px;margin-bottom:8px;flex-wrap:wrap;align-items:center">' + wb + wstats + '<span style="margin-left:auto;font-size:11px">📊 待' + wp + ' 进行' + wg + '</span>' + (hp('manage_tasks') ? '<button class="btn btn-primary btn-sm" onclick="dpk()">+ 派单</button>' : '') + '</div><div class="panel"><div class="panel-body" style="overflow-x:auto"><table style="font-size:10px"><thead><tr><th style="min-width:60px;position:sticky;left:0">组长</th>' + dh + '</tr></thead><tbody>' + lr2 + '</tbody></table></div></div>';
    $('#headerActions').innerHTML = '';
}
async function dpk() {
    await lr();
    var tsks = await aj('/api/tasks');
    var pts = tsks.filter(function(t) { return t.status === 'pending'; });
    if (!pts.length) { ts('暂无待分配任务'); return; }
    var lo = pc.filter(function(p) { return p.role === '采样组长' && p.status === 'active'; }).map(function(p) { return '<option value="' + p.id + '">' + p.name + '</option>'; }).join('');
    var list = pts.map(function(t) { return '<tr><td><input type="checkbox" class="dp-cb" value="' + t.id + '"></td><td><strong>' + t.pid + '</strong></td><td>' + (t.task_name || '-') + '</td><td>' + (t.company || '-') + '</td></tr>'; }).join('');
    sm('派单', '<div class="form-row"><div class="form-group"><label>开始日期 *</label><input type="date" id="dp_s"></div><div class="form-group"><label>结束日期 *</label><input type="date" id="dp_e"></div></div><div class="form-row"><div class="form-group"><label>采样组长 *</label><select id="dp_l" onchange="ldm2(this.value)"><option value="">— 请选择 —</option>' + lo + '</select></div><div class="form-group" id="dp_member_wrap" style="display:none"><label>采样组员</label><select id="dp_m" multiple style="height:100px;width:100%"></select></div></div><div style="max-height:200px;overflow-y:auto;margin-top:10px"><table><thead><tr><th>选</th><th>编号</th><th>任务名</th><th>企业</th></tr></thead><tbody>' + list + '</tbody></table></div>', '<button class="btn" onclick="clm()">取消</button><button class="btn btn-primary" onclick="dpa()">确认派单</button>');
}
function ldm2(lid) {
    var wrap = $('#dp_member_wrap');
    var sel = $('#dp_m');
    if (!lid) { wrap.style.display = 'none'; return; }
    wrap.style.display = '';
    // 排除组长本人，列出其他人员，绑定组员默认选中
    var boundIds = pc.filter(function(x) { return x.leader_id === parseInt(lid); }).map(function(x) { return x.id; });
    sel.innerHTML = pc.filter(function(x) { return x.status === 'active' && x.id !== parseInt(lid); }).map(function(x) {
        var s = boundIds.indexOf(x.id) >= 0 ? ' selected' : '';
        return '<option value="' + x.id + '"' + s + '>' + x.name + ' (' + x.role + ')</option>';
    }).join('');
    // 点击切换选中状态
    sel.onmousedown = function(e) {
        e.preventDefault();
        var opt = e.target;
        if (opt.tagName === 'OPTION') {
            opt.selected = !opt.selected;
            // 触发 change 事件
            var ev = document.createEvent('HTMLEvents');
            ev.initEvent('change', false, true);
            sel.dispatchEvent(ev);
        }
    };
}
async function dpa() { var ds = $('#dp_s').value, de = $('#dp_e').value, lid = $('#dp_l').value; if (!ds || !de || !lid) { ts('请填写日期和组长'); return; } var mids = Array.from($('#dp_m').selectedOptions).map(function(o) { return o.value; }).join(','); var cbs = document.querySelectorAll('.dp-cb:checked'); if (!cbs.length) { ts('请选择任务'); return; } for (var i = 0; i < cbs.length; i++) await aj('/api/tasks/' + cbs[i].value, { m: 'PUT', b: JSON.stringify({ date_start: ds, date_end: de, leader_ids: lid, member_ids: mids, status: 'progress' }) }); clm(); ts('✅ 已派单 ' + cbs.length + ' 个'); bm(dy, dm); }
// 派单计划中点击任务卡片
async function dpt(tid) {
    await lr();
    var tsks = await aj('/api/tasks');
    var t = tsks.find(function(x) { return x.id === tid; });
    if (!t) { ts('任务不存在'); return; }
    var isAdmin = hp('manage_tasks');
    var ft = [];
    if (isAdmin) {
        ft.push('<button class="btn btn-warning" onclick="clm();dptCancel(' + tid + ')">🚫 取消派单</button>');
        ft.push('<button class="btn" onclick="clm();dptReassign(' + tid + ')">🔄 改派</button>');
    }
    ft.push('<button class="btn btn-ghost" onclick="clm();vt(' + tid + ')">📋 查看详情</button>');
    ft.push('<button class="btn" onclick="clm()">关闭</button>');
    sm('📌 ' + t.pid + ' · ' + (t.task_name || '未命名'),
        '<div style="font-size:13px;margin-bottom:10px">' +
        '<div><strong>项目类别：</strong>' + (t.project_type || '-') + ' &nbsp; <strong>有效期：</strong>' + (t.valid_period || '-') + '</div>' +
        '<div><strong>地区：</strong>' + (t.district || '-') + '</div>' +
        '<div><strong>日期：</strong>' + (t.date_start || '?') + ' ~ ' + (t.date_end || '?') + '</div>' +
        '<div><strong>组长：</strong>' + (t.leader_names || '-') + ' &nbsp; <strong>组员：</strong>' + (t.member_names || '无') + '</div>' +
        '<div><strong>状态：</strong>' + stg(t.status) + '</div></div>',
        ft.join(' '));
}
async function dptCancel(tid) {
    if (!confirm('确认取消该任务的派单？任务将回到待分配状态。')) return;
    await aj('/api/tasks/' + tid, { m: 'PUT', b: JSON.stringify({ status: 'pending', leader_ids: '', member_ids: '', date_start: null, date_end: null }) });
    ts('✅ 已取消派单');
    bm(dy, dm);
}
async function dptReassign(tid) {
    await lr();
    var tsks = await aj('/api/tasks');
    var t = tsks.find(function(x) { return x.id === tid; });
    if (!t) return;
    var lo = pc.filter(function(p) { return p.role === '采样组长' && p.status === 'active'; }).map(function(p) { return '<option value="' + p.id + '">' + p.name + '</option>'; }).join('');
    sm('🔄 改派 ' + t.pid,
        '<input type="hidden" id="dpr_id" value="' + tid + '">' +
        '<div class="form-row"><div class="form-group"><label>开始日期</label><input type="date" id="dpr_s" value="' + (t.date_start || '') + '"></div><div class="form-group"><label>结束日期</label><input type="date" id="dpr_e" value="' + (t.date_end || '') + '"></div></div>' +
        '<div class="form-row"><div class="form-group"><label>新组长</label><select id="dpr_l" onchange="ldm2Reassign(this.value)"><option value="">— 请选择 —</option>' + lo + '</select></div><div class="form-group" id="dpr_member_wrap" style="display:none"><label>组员</label><select id="dpr_m" multiple style="height:100px;width:100%"></select></div></div>',
        '<button class="btn" onclick="clm()">取消</button><button class="btn btn-primary" onclick="dprSave()">确认改派</button>');
    // Pre-select current leader if any
    if (t.leader_ids) { setTimeout(function() { $('#dpr_l').value = t.leader_ids; ldm2Reassign(t.leader_ids); if (t.member_ids) { setTimeout(function() { var mids = t.member_ids.split(','); var sel = $('#dpr_m'); Array.from(sel.options).forEach(function(o) { if (mids.indexOf(o.value) >= 0) o.selected = true; }); }, 100); } }, 50); }
}
function ldm2Reassign(lid) {
    var wrap = $('#dpr_member_wrap'), sel = $('#dpr_m');
    if (!lid) { wrap.style.display = 'none'; return; }
    wrap.style.display = '';
    var boundIds = pc.filter(function(x) { return x.leader_id === parseInt(lid); }).map(function(x) { return x.id; });
    sel.innerHTML = pc.filter(function(x) { return x.status === 'active' && x.id !== parseInt(lid); }).map(function(x) {
        var s = boundIds.indexOf(x.id) >= 0 ? ' selected' : '';
        return '<option value="' + x.id + '"' + s + '>' + x.name + ' (' + x.role + ')</option>';
    }).join('');
    sel.onmousedown = function(e) {
        e.preventDefault();
        var opt = e.target;
        if (opt.tagName === 'OPTION') { opt.selected = !opt.selected; var ev = document.createEvent('HTMLEvents'); ev.initEvent('change', false, true); sel.dispatchEvent(ev); }
    };
}
async function dprSave() {
    var tid = $('#dpr_id').value, ds = $('#dpr_s').value, de = $('#dpr_e').value, lid = $('#dpr_l').value;
    if (!ds || !de || !lid) { ts('请填写日期和新组长'); return; }
    var mids = Array.from($('#dpr_m').selectedOptions).map(function(o) { return o.value; }).join(',');
    await aj('/api/tasks/' + tid, { m: 'PUT', b: JSON.stringify({ date_start: ds, date_end: de, leader_ids: lid, member_ids: mids }) });
    clm();
    ts('✅ 已改派');
    bm(dy, dm);
}

// Personnel
var psrch = '';
async function rps(sr) { if (sr !== undefined) psrch = sr || ''; await lr(); var tsks = await aj('/api/tasks'); var p = psrch ? '?search=' + encodeURIComponent(psrch) : ''; var list = psrch ? await aj('/api/personnel' + p) : pc; var h = '<div style="display:flex;gap:6px;margin-bottom:10px;align-items:center"><button class="btn btn-primary btn-sm" onclick="spf()">+ 添加人员</button><div class="search-box" style="margin-left:auto"><input type="text" id="ps" placeholder="🔍 搜索..." value="' + psrch + '"><button class="btn btn-sm" onclick="psrch=$(\'#ps\').value;rps(psrch)">搜索</button>' + (psrch ? '<button class="btn btn-sm btn-ghost" onclick="psrch=\'\';rps(\'\')">清除</button>' : '') + '</div></div><div class="panel"><div class="panel-body"><table><thead><tr><th>姓名</th><th>角色</th><th>归属组长</th><th>电话</th><th>状态</th><th>账号</th><th>注册码</th><th>操作</th></tr></thead><tbody>'; list.forEach(function(p) { var as = p.has_account ? '<span class="tag tag-success">' + (p.account_username || '已注册') + '</span>' : '<span class="tag tag-warning">未注册</span>'; var rl = !p.has_account && p.reg_code ? '<code style="cursor:pointer" onclick="crl(\'' + p.reg_code + '\')">' + p.reg_code + '</code>' : '-'; h += '<tr><td><strong>' + p.name + '</strong></td><td><span class="tag tag-info">' + p.role + '</span></td><td>' + (p.leader_name || '-') + '</td><td>' + (p.phone || '-') + '</td><td>' + (p.status === 'active' ? '<span class="tag tag-success">在职</span>' : '<span class="tag tag-default">离职</span>') + '</td><td>' + as + '</td><td>' + rl + '</td><td><button class="btn btn-sm" onclick="epf(' + p.id + ')">编辑</button>' + (p.status === 'active' && !p.has_account ? '<button class="btn btn-sm" onclick="rgc(' + p.id + ')">重置</button>' : '') + '<button class="btn btn-sm btn-danger" onclick="dlp(' + p.id + ',\'' + p.name.replace(/'/g, "\\'") + '\')">删除</button></td></tr>'; }); h += '</tbody></table></div></div>'; $('#contentArea').innerHTML = h; $('#headerActions').innerHTML = ''; }
function crl(code) { var u = location.origin + '/register?code=' + code; navigator.clipboard.writeText(u).then(function() { ts('📋 已复制'); }).catch(function() { prompt('复制:', u); }); }
async function rgc(id) { var r = await aj('/api/personnel/' + id + '/regenerate-code', { m: 'POST' }); ts('✅ 新码: ' + r.reg_code); rps(); }
function spf(pid) { var p = pid ? pc.find(function(x) { return x.id === pid; }) : null; var cr = p ? p.role : '采样组员'; var lds = pc.filter(function(x) { return x.role === '采样组长' && x.status === 'active'; }).map(function(x) { return '<option value="' + x.id + '"' + (p && p.leader_id === x.id ? ' selected' : '') + '>' + x.name + '</option>'; }).join(''); var ldStyle = cr === '采样组员' ? '' : 'display:none'; sm(p ? '编辑' : '添加人员', '<input type="hidden" id="pf_id" value="' + (p ? p.id : '') + '"><div class="form-row"><div class="form-group"><label>姓名 *</label><input id="pf_name" value="' + (p ? p.name : '') + '"></div><div class="form-group"><label>角色</label><select id="pf_role" onchange="document.getElementById(\'ld-grp\').style.display=this.value===\'采样组员\'?\'\':\'none\'"><option value="采样组长"' + (cr === '采样组长' ? ' selected' : '') + '>采样组长</option><option value="采样组员"' + (cr === '采样组员' ? ' selected' : '') + '>采样组员</option><option value="现场部部长"' + (cr === '现场部部长' ? ' selected' : '') + '>现场部部长</option><option value="报告部负责人"' + (cr === '报告部负责人' ? ' selected' : '') + '>报告部负责人</option><option value="实验部负责人"' + (cr === '实验部负责人' ? ' selected' : '') + '>实验部负责人</option></select></div></div><div class="form-row"><div class="form-group"><label>电话</label><input id="pf_phone" value="' + (p ? p.phone || '' : '') + '"></div><div class="form-group" id="ld-grp" style="' + ldStyle + '"><label>归属组长</label><select id="pf_leader"><option value="">无</option>' + lds + '</select></div></div>', '<button class="btn" onclick="clm()">取消</button><button class="btn btn-primary" onclick="svp()">保存</button>'); if (p) { $('#pf_role').value = p.role; $('#pf_leader').value = p.leader_id || ''; } }
async function svp() { var id = $('#pf_id').value, n = $('#pf_name').value; if (!n) { ts('请输入姓名'); return; } var d = { name: n, role: $('#pf_role').value, phone: $('#pf_phone').value, leader_id: parseInt($('#pf_leader').value) || null }; if (id) { await aj('/api/personnel/' + id, { m: 'PUT', b: JSON.stringify(d) }); } else { var r = await aj('/api/personnel', { m: 'POST', b: JSON.stringify(d) }); clm(); rps(); crl(r.reg_code); return; } clm(); rps(); ts('✅ 已保存'); }
function epf(id) { spf(id); }
async function dlp(id, name) { if (!confirm('确认删除人员「' + name + '」？\n\n如有关联账号将被同时删除。')) return; await aj('/api/personnel/' + id, { m: 'DELETE' }); pc = []; ts('🗑️ 已删除 ' + name); rps(); }

// Users (minimal)
async function rus() { var us = await aj('/api/users'); var h = '<div class="panel"><div class="panel-body"><table><thead><tr><th>用户名</th><th>显示名</th><th>角色</th><th>电话</th><th>状态</th><th>操作</th></tr></thead><tbody>'; us.forEach(function(u) { h += '<tr><td><strong>' + u.username + '</strong></td><td>' + u.display_name + '</td><td><span class="tag tag-info">' + u.role + '</span></td><td>' + (u.phone || '-') + '</td><td>' + (u.status === 'active' ? '<span class="tag tag-success">正常</span>' : '<span class="tag tag-default">停用</span>') + '</td><td><button class="btn btn-sm" onclick="alert(\'编辑功能\')">编辑</button></td></tr>'; }); h += '</tbody></table></div></div>'; $('#contentArea').innerHTML = h; $('#headerActions').innerHTML = ''; }

// My Tasks
async function rmt() { var tsks = await aj('/api/tasks'); var h = '<div class="panel"><div class="panel-body"><table><thead><tr><th>编号</th><th>任务名</th><th>企业</th><th>日期</th><th>状态</th><th>操作</th></tr></thead><tbody>'; tsks.forEach(function(t) { h += '<tr style="cursor:pointer" onclick="vt(' + t.id + ')"><td><strong>' + t.pid + '</strong></td><td>' + (t.task_name || '-') + '</td><td>' + (t.company || '-') + '</td><td>' + (t.date_start ? fd(t.date_start) + '~' + fd(t.date_end) : '未派单') + '</td><td>' + stg(t.status) + '</td><td>' + (t.status === 'pending' ? '<button class="btn btn-primary btn-sm" onclick="event.stopPropagation();smt(' + t.id + ')">开始</button>' : '') + '</td></tr>'; }); h += '</tbody></table></div></div>'; $('#contentArea').innerHTML = h; $('#headerActions').innerHTML = ''; }
async function smt(id) { await aj('/api/tasks/' + id, { m: 'PUT', b: JSON.stringify({ status: 'progress' }) }); rmt(); ts('✅ 已开始'); }

// Render
async function rp(p) {
    try {
        var renders = { dashboard: rd, tasks: function() { return rts(); }, dispatch: rds, personnel: function() { return rps(); }, users: rus, mytasks: rmt };
        if (renders[p]) await renders[p]();
    } catch (e) { var ca = $('#contentArea'); if (ca) ca.innerHTML = '<div style="padding:40px;text-align:center;color:#ff4d4f"><h3>⚠️ 错误</h3><p>' + e.message + '</p></div>'; }
    uru();
}

// Init
$$('.nav-item').forEach(function(item) {
    item.addEventListener('click', function() { var p = this.dataset.page; if (p) nav(p); });
});
uru();
var sp = (location.hash || '#dashboard').replace('#', '');
nav(sp);
