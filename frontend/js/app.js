import {mountAmbient} from './ambient.js?v=3.0.0';
import {api,session} from './api.js';
import {esc,icon,field,toast,dateKey} from './ui.js';
import {brand,landscape,shell,routeMeta,dashboard,tasksView,calendar,peopleView,usersView,filteredTasks} from './views.js?v=3.0.0';
import {createActions} from './forms.js?v=3.0.0';
const state={user:null,tasks:[],people:[],users:[],meta:{roles:[],permissions:[],templates:{}},route:'dashboard',month:new Date(),selectedDate:dateKey(new Date()),dashTab:'today',page:1,filter:{status:'',search:'',district:'',period:''}};
const can=permission=>state.user?.role==='admin'||!!state.user?.permissions?.[permission];
const actions=createActions(state,can,refresh);
function login(register=location.pathname.startsWith('/register')) {
 document.querySelector('#dialog').close();
 document.querySelector('#app').innerHTML=`<div class="login-page"><section class="login-story">${brand}<div class="login-manifesto"><h1>现场有序，<br>协作有光。</h1><p>连接任务、团队与现场<br>让环境监测工作，在一个空间内有序开展。</p></div><canvas data-ambient aria-hidden="true"></canvas><footer>XINGYUAN · 环境监测采样协作平台</footer></section><form class="login-form"><h2>${register?'加入采样团队':'欢迎回来'}</h2><p>${register?'使用管理员提供的注册码创建账号。':'登录工作空间，开始今天的监测工作。'}</p>${register?field('reg_code','注册码',new URLSearchParams(location.search).get('code')||'','text','required minlength="6"'):''}${field('username','用户名',register?'':'admin','text','required autocomplete="username"')}${field('password','密码','','password','required autocomplete="'+(register?'new-password':'current-password')+'" minlength="4"')}<button class="button primary" type="submit">${register?'创建账号':'登录工作空间'} ${icon('arrow',16)}</button><div class="form-error" style="padding:15px 0" role="alert"></div><div class="login-hint">${register?'<a href="/login">已有账号？返回登录</a>':'首次使用？<a href="/register">使用注册码加入</a>'}<br>星源 · 让每一次监测更有价值</div></form></div>`;
 mountAmbient();
 document.querySelector('.login-form').onsubmit=async e=>{e.preventDefault();const b=e.submitter;b.disabled=true;const data=Object.fromEntries(new FormData(e.target));try{if(register){await api('/auth/register','POST',data);toast('注册成功，请登录');login(false);}else{const result=await api('/auth/login','POST',data);session.set(result.access_token);await boot();}}catch(error){document.querySelector('.login-form .form-error').textContent=error.message;}finally{b.disabled=false;}};
}
async function refresh() {
 const [tasks,people]=await Promise.all([api('/tasks'),api('/personnel')]);
 state.tasks=tasks;state.people=people;
 if(can('manage_users'))state.users=await api('/users');
 render();
}
function render(){
 if(!state.user||!session.get())return;
 state.route=location.hash.slice(1)||'dashboard';
 if(!routeMeta[state.route]||(state.route==='users'&&!can('manage_users'))||(state.route==='dispatch'&&!can('view_dispatch')))state.route='dashboard';
 document.querySelector('#app').innerHTML=shell(state,can);
 renderPage();
}
function renderPage(){
 const views={dashboard:()=>dashboard(state),tasks:()=>tasksView(state),dispatch:()=>calendar(state,true),personnel:()=>peopleView(state,can),users:()=>usersView(state)};
 document.querySelector('#page').innerHTML=views[state.route]();
 mountAmbient();
 const search=document.querySelector('#task-search');if(search)search.oninput=e=>{state.filter.search=e.target.value;state.page=1;const pos=e.target.selectionStart;renderPage();const input=document.querySelector('#task-search');input.focus();input.setSelectionRange(pos,pos);};
 for(const [id,key] of [['district-filter','district'],['period-filter','period']]){const node=document.getElementById(id);if(node)node.onchange=()=>{state.filter[key]=node.value;state.page=1;renderPage();};}
}
document.addEventListener('click',async e=>{
 const el=e.target.closest('button,a');if(!el)return;
 try{
 if(el.dataset.action){const action=el.dataset.action;if(action==='logout'){session.clear();state.user=null;login(false);}else if(action==='menu'){const open=document.querySelector('.sidebar').classList.toggle('open');document.querySelector('.mobile-menu').setAttribute('aria-expanded',String(open));if(!open)document.querySelector('.mobile-menu').focus();}else if(action==='reset-filter'){state.filter={status:'',search:'',district:'',period:''};renderPage();}else if(action==='export'){actions.exportTasks(state.route==='tasks'?filteredTasks(state):state.tasks);}else if(actions[action])await actions[action]();}
 if(el.dataset.task)await actions.detail(Number(el.dataset.task));
 if(el.dataset.person)actions.person(Number(el.dataset.person));
 if(el.dataset.user)actions.user(Number(el.dataset.user));
 if(el.dataset.invite)await actions.invite(Number(el.dataset.invite));
 if(el.dataset.deletePerson)actions.remove('personnel',Number(el.dataset.deletePerson));
 if(el.dataset.deleteUser)actions.remove('users',Number(el.dataset.deleteUser));
 if(el.dataset.dashTab){state.dashTab=el.dataset.dashTab;renderPage();}
 if(el.dataset.status!==undefined){state.filter.status=el.dataset.status;state.page=1;renderPage();}
 if(el.dataset.page){state.page+=Number(el.dataset.page);renderPage();}
 if(el.dataset.month!==undefined){if(Number(el.dataset.month)===0){state.month=new Date();state.selectedDate=dateKey(state.month);state.dashTab='today';}else{state.month=new Date(state.month.getFullYear(),state.month.getMonth()+Number(el.dataset.month),1);}renderPage();}
 if(el.dataset.date){state.selectedDate=el.dataset.date;state.dashTab='today';renderPage();}
 }catch(error){toast(error.message);}
});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&document.querySelector('.sidebar.open')){document.querySelector('.sidebar').classList.remove('open');const menu=document.querySelector('.mobile-menu');menu.setAttribute('aria-expanded','false');menu.focus();}});
window.addEventListener('hashchange',render);
window.addEventListener('session-expired',()=>{if(state.user){state.user=null;login(false);toast('登录已过期，请重新登录');}});
async function boot(){try{state.user=await api('/auth/me');state.meta=await api('/meta/permissions');await refresh();}catch(error){login(false);toast(error.message);}}
if(session.get())boot();else login();

