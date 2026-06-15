#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import secrets
import sqlite3
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
DB = ROOT / "lulu.db"
FAVICON = ROOT / "favicon.gif"
HOST = "127.0.0.1"
PORT = 8099
ADMIN_USER = "admin"
ADMIN_PASSWORD = "yu726622"
ADMIN_SESSIONS = set()

DEFAULT_DISHES = [
    ("招牌推荐", "噜噜红烧肉", 38, "五花肉慢炖收汁，肥而不腻。", "肉", 18, 0),
    ("招牌推荐", "酸菜鱼", 58, "现片鱼肉，酸香开胃。", "鱼", 12, 0),
    ("招牌推荐", "香辣口水鸡", 32, "红油花生碎，凉菜热味。", "鸡", 16, 0),
    ("招牌推荐", "麻婆豆腐", 26, "嫩豆腐配牛肉末，麻辣鲜香。", "豆", 20, 0),
    ("家常热炒", "番茄炒蛋", 22, "酸甜下饭，老少皆宜。", "蛋", 25, 0),
    ("家常热炒", "酸辣土豆丝", 18, "脆口爽利，默认微辣。", "土", 30, 0),
    ("家常热炒", "小炒黄牛肉", 46, "香芹辣椒快炒，锅气很足。", "牛", 10, 0),
    ("主食汤饮", "米饭", 3, "东北珍珠米，一碗起点。", "饭", 80, 0),
    ("主食汤饮", "紫菜蛋花汤", 12, "清淡暖胃，适合搭配热炒。", "汤", 24, 0),
    ("主食汤饮", "冰柠檬茶", 10, "清爽解辣，甜度固定。", "茶", 40, 0),
]

INDEX_HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>噜噜菜馆</title>
  <link rel="icon" type="image/gif" href="/favicon.gif">
  <link rel="shortcut icon" type="image/gif" href="/favicon.gif">
  <style>
    :root{--bg:#f6f4ee;--panel:#fff;--ink:#20242c;--muted:#6d7683;--line:#dfe3e8;--brand:#0f766e;--brand2:#0a5e57;--accent:#d84b31;--soft:#eef7f5;--warn:#b97513;--ok:#168452;--shadow:0 16px 42px rgba(32,36,44,.12)}
    *{box-sizing:border-box}[hidden]{display:none!important}.view:not(.active){display:none!important}body{margin:0;color:var(--ink);background:linear-gradient(120deg,rgba(15,118,110,.12),transparent 36%),linear-gradient(300deg,rgba(216,75,49,.11),transparent 32%),var(--bg);font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}button,input,select,textarea{font:inherit}button{cursor:pointer}button:disabled{opacity:.55;cursor:not-allowed}.app{width:min(1280px,calc(100% - 28px));margin:auto;padding:22px 0 36px}header{display:grid;grid-template-columns:1fr auto;gap:18px;align-items:end;padding:22px 0 18px}.tag{width:fit-content;padding:6px 10px;border-radius:8px;color:var(--brand2);background:rgba(15,118,110,.13);font-size:13px;font-weight:850}h1{margin:10px 0 8px;font-size:clamp(42px,8vw,82px);line-height:.95;letter-spacing:0}.summary{max-width:760px;margin:0;color:var(--muted);font-size:17px;line-height:1.65}.top{min-width:340px;display:grid;gap:8px;padding:14px;border:1px solid var(--line);border-radius:8px;background:rgba(255,255,255,.78);box-shadow:var(--shadow)}.row{display:flex;gap:8px;flex-wrap:wrap}.login{display:grid;grid-template-columns:1fr 1fr auto;gap:8px}.btn,.pill{min-height:40px;border-radius:8px;padding:0 13px;font-weight:850;white-space:nowrap}.btn{border:0;color:#fff;background:var(--brand)}.ghost,.pill{min-height:40px;border:1px solid var(--line);border-radius:8px;padding:0 13px;color:var(--ink);background:#fff;font-weight:850}.pill.active{color:#fff;border-color:var(--brand);background:var(--brand)}.danger{border:1px solid rgba(216,75,49,.35);color:var(--accent);background:#fff}.field{min-height:40px;border:1px solid var(--line);border-radius:8px;padding:0 12px;background:#fff;color:var(--ink)}.userline{color:var(--muted);font-size:14px;line-height:1.45}.view{display:none}.view.active{display:block}.layout{display:grid;grid-template-columns:1fr 390px;gap:18px;align-items:start}.panel{border:1px solid var(--line);border-radius:8px;background:var(--panel);box-shadow:0 10px 30px rgba(32,36,44,.08);overflow:hidden}.scan{display:grid;grid-template-columns:86px 1fr auto;align-items:center;gap:14px;padding:14px;margin-bottom:14px}.qr{width:86px;height:86px;display:grid;grid-template-columns:repeat(5,1fr);gap:4px;padding:8px;border:1px solid var(--line);border-radius:8px;background:#fff}.qr span{background:var(--ink);border-radius:2px}.qr span:nth-child(2n){opacity:.25}h2{margin:0;font-size:20px}.scan p,.note{margin:6px 0 0;color:var(--muted);line-height:1.5}.table{color:var(--accent);font-weight:950}.filters{position:sticky;top:0;z-index:5;display:grid;gap:10px;padding:10px 0;background:linear-gradient(var(--bg),rgba(246,244,238,.86));backdrop-filter:blur(10px)}.search{width:100%}.tabs{display:flex;gap:8px;overflow:auto;padding-bottom:2px}.menu{display:grid;gap:18px}.section-title{margin:12px 0 10px;font-size:24px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.dish{min-height:225px;display:grid;grid-template-columns:112px 1fr;gap:14px;padding:12px;border:1px solid var(--line);border-radius:8px;background:#fff;box-shadow:0 8px 22px rgba(32,36,44,.07)}.dish.sold{filter:grayscale(.9);opacity:.65}.photo{width:112px;min-height:112px;overflow:hidden;border-radius:8px;display:grid;place-items:center;flex:0 0 auto;color:#fff;font-size:34px;font-weight:950;background:radial-gradient(circle at 28% 24%,rgba(255,255,255,.35),transparent 22%),linear-gradient(135deg,var(--brand),var(--accent))}.photo img{width:100%;height:100%;min-height:112px;object-fit:cover;display:block}.dishinfo{min-width:0;display:grid;gap:8px}.dishhead{display:flex;justify-content:space-between;gap:10px}.name{font-size:18px;font-weight:950;line-height:1.25}.price{color:var(--accent);font-size:18px;font-weight:950;white-space:nowrap}.desc{margin:0;color:var(--muted);font-size:14px;line-height:1.5}.opt{display:grid;grid-template-columns:48px 1fr;align-items:center;gap:8px;font-size:13px}.opt label{color:var(--muted);font-weight:850}select{width:100%;min-height:36px;border:1px solid var(--line);border-radius:8px;padding:0 10px;background:#fff}.checks{display:flex;flex-wrap:wrap;gap:6px}.check{display:inline-flex;align-items:center;gap:4px;min-height:30px;padding:0 8px;border:1px solid var(--line);border-radius:8px;background:#fff;color:var(--muted);font-size:12px;font-weight:850}.actions{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-top:auto}.mini{min-height:34px;border:1px solid var(--line);border-radius:8px;padding:0 10px;background:#fff;color:var(--ink);font-size:13px;font-weight:850}.mini.primary{border:0;color:#fff;background:var(--brand)}.cart{position:sticky;top:12px;border:1px solid var(--line);border-radius:8px;background:#fff;box-shadow:var(--shadow);overflow:hidden}.carthead,.cartfoot{padding:15px;background:var(--soft)}.carthead{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--line)}.badge{min-width:32px;height:32px;display:grid;place-items:center;border-radius:8px;color:#fff;background:var(--accent);font-weight:950}.cartlist{min-height:190px;max-height:390px;overflow:auto;padding:10px 15px}.empty{min-height:150px;display:grid;place-items:center;color:var(--muted);text-align:center;line-height:1.5}.cartitem{display:grid;grid-template-columns:1fr auto;gap:8px;padding:12px 0;border-bottom:1px solid var(--line)}.cartitem:last-child{border-bottom:0}.cartitem small{display:block;color:var(--muted);line-height:1.45}textarea{width:100%;min-height:78px;resize:vertical;border:1px solid var(--line);border-radius:8px;padding:10px;background:#fff}.total{display:flex;align-items:center;justify-content:space-between;gap:12px;margin:12px 0;font-weight:950}.total strong{color:var(--accent);font-size:28px}.toast{min-height:22px;color:var(--brand2);font-size:14px;font-weight:850;line-height:1.5}.history,.merchant{display:grid;gap:14px}.merchantgrid{display:grid;grid-template-columns:380px 1fr;gap:16px;align-items:start}.manager{padding:15px}.formgrid{display:grid;gap:10px;margin-top:12px}.label{display:grid;gap:6px}.label span{color:var(--muted);font-size:13px;font-weight:850}.list{display:grid;gap:10px}.card{padding:14px;border:1px solid var(--line);border-radius:8px;background:#fff;box-shadow:0 8px 22px rgba(32,36,44,.07)}.cardtop{display:flex;justify-content:space-between;gap:12px;margin-bottom:10px}.meta{color:var(--muted);font-size:13px;line-height:1.55}.state{display:inline-flex;min-height:28px;align-items:center;padding:0 9px;border-radius:8px;color:var(--brand2);background:rgba(15,118,110,.13);font-size:13px;font-weight:900}.state.warn{color:var(--warn);background:rgba(185,117,19,.13)}.state.done{color:var(--ok);background:rgba(22,132,82,.13)}.adminactions{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}@media(max-width:1050px){header,.layout,.merchantgrid{grid-template-columns:1fr}.top{min-width:0}.cart{position:static}}@media(max-width:690px){.app{width:min(100% - 20px,1280px);padding-top:10px}.login,.scan{grid-template-columns:1fr}.qr{display:none}.grid{grid-template-columns:1fr}.dish{grid-template-columns:86px 1fr}.photo{width:86px;min-height:86px;font-size:26px}.photo img{min-height:86px}.dishhead,.opt{display:grid;grid-template-columns:1fr}}
  </style>
</head>
<body data-admin="0">
  <div class="app">
    <header>
      <div>
        <div class="tag">家常烟火味 · 新鲜现炒 · 热乎上桌</div>
        <h1>噜噜菜馆</h1>
        <p class="summary">噜噜菜馆用心做好每一道家常菜，现点现炒、鲜香入味，让一桌人吃得踏实又满足。</p>
      </div>
      <div class="top">
        <div class="row" id="merchantTools" hidden>
          <button class="pill active" data-view="customer">顾客点餐</button>
          <button class="pill" data-view="merchant">商家后台</button>
        </div>
        <div class="login">
          <input class="field" id="loginName" placeholder="姓名">
          <input class="field" id="loginPhone" placeholder="手机号">
          <button class="btn" id="loginBtn">登录</button>
        </div>
        <div class="row">
          <button class="ghost" id="logoutBtn">退出登录</button>
          <button class="ghost" id="notifyBtn" hidden>开启商家通知</button>
        </div>
        <div class="userline" id="userLine"></div>
      </div>
    </header>
    <section class="view active" id="customerView">
      <div class="layout">
        <main>
          <section class="filters">
            <input class="field search" id="search" placeholder="搜索菜名、描述或分类">
            <div class="tabs" id="tabs"></div>
          </section>
          <div class="menu" id="menu"></div>
          <section class="history panel manager" style="margin-top:16px">
            <h2>我的历史订单</h2>
            <div class="note">登录后可查看服务器保存的历史订单和状态。</div>
            <div class="list" id="history"></div>
          </section>
        </main>
        <aside class="cart">
          <div class="carthead"><h2>购物车</h2><span class="badge" id="cartCount">0</span></div>
          <div class="cartlist" id="cartList"></div>
          <div class="cartfoot">
            <textarea id="note" placeholder="订单备注：少油、先上米饭、打包等"></textarea>
            <div class="total"><span>合计</span><strong id="total">¥0</strong></div>
            <div class="row"><button class="btn" id="submit">提交订单并通知商家</button><button class="ghost" id="clearCart">清空</button></div>
            <div class="toast" id="toast"></div>
          </div>
        </aside>
      </div>
    </section>
    <section class="view merchant" id="merchantView">
      <div class="merchantgrid">
        <aside class="panel manager">
          <h2>菜品管理</h2>
          <div class="note">添加/删除菜品、设置售罄、修改库存、批量调价。</div>
          <div class="formgrid">
            <label class="label"><span>菜品名</span><input class="field" id="dishName"></label>
            <label class="label"><span>分类</span><input class="field" id="dishCategory"></label>
            <label class="label"><span>价格</span><input class="field" id="dishPrice" type="number"></label>
            <label class="label"><span>图片</span><input class="field" id="dishImage" placeholder="图片 URL、emoji 或单字"></label>
            <label class="label"><span>描述</span><textarea id="dishDesc"></textarea></label>
            <button class="btn" id="addDish">添加菜品</button>
            <div class="row"><input class="field" id="batchValue" type="number" placeholder="批量调价金额"><button class="ghost" id="batchPrice">全部调价</button></div>
          </div>
        </aside>
        <main class="merchant">
          <section class="panel manager">
            <div class="cardtop"><div><h2>实时订单</h2><div class="note">有新订单会提示并响铃。状态可改为已下单、待出餐、已完成。</div></div><button class="ghost" id="refreshOrders">刷新</button></div>
            <div class="list" id="orders"></div>
          </section>
          <section class="panel manager">
            <h2>菜品与库存</h2>
            <div class="list" id="adminDishes"></div>
          </section>
        </main>
      </div>
    </section>
  </div>
  <script>
    const api = (url, opts={}) => fetch(url, {headers:{'Content-Type':'application/json'}, ...opts}).then(async r => { const d = await r.json().catch(()=>({})); if(!r.ok) throw new Error(d.error || '请求失败'); return d; });
    const state = { isAdmin: document.body.dataset.admin === '1', user: JSON.parse(localStorage.getItem('lulu_user') || 'null'), dishes: [], orders: [], cart: [], category: '全部', query: '', seenOrders: new Set(), notify: false };
    const $ = s => document.querySelector(s);
    const money = v => `¥${Number(v).toFixed(0)}`;
    const total = () => state.cart.reduce((s,i)=>s+i.price*i.quantity,0);
    const cats = () => ['全部', ...Array.from(new Set(state.dishes.map(d=>d.category)))];
    const toast = text => { $('#toast').textContent = text; setTimeout(()=>{ if($('#toast').textContent===text) $('#toast').textContent=''; }, 3200); };
    const itemKey = i => [i.dish_id,i.size,i.spicy,i.avoid.join(',')].join('|');
    const photo = d => /^https?:\/\//i.test(d.image||'') ? `<img src="${d.image}" alt="${d.name}" loading="lazy">` : (d.image||d.name[0]);
    function selected(id){ return { size:$(`#size-${id}`)?.value||'标准', spicy:$(`#spicy-${id}`)?.value||'不辣', avoid:Array.from(document.querySelectorAll(`[data-avoid="${id}"]:checked`)).map(x=>x.value) }; }
    function price(d,s){ return s==='大份'?d.price+8:s==='小份'?Math.max(1,d.price-4):d.price; }
    function qty(id){ return state.cart.filter(i=>i.dish_id===id).reduce((s,i)=>s+i.quantity,0); }
    function renderShell(){ $('#userLine').textContent=state.isAdmin?'已进入商家后台':(state.user?`已登录：${state.user.name} · ${state.user.phone}`:'未登录；浏览菜单可以，下单前需要登录。'); $('#loginName').value=state.user?.name||''; $('#loginPhone').value=state.user?.phone||''; renderTabs(); renderMenu(); renderCart(); renderHistory(); if(state.isAdmin){ renderOrders(false); renderAdminDishes(); } }
    function renderTabs(){ $('#tabs').innerHTML=cats().map(c=>`<button class="pill ${c===state.category?'active':''}" data-cat="${c}">${c}</button>`).join(''); }
    function filtered(){ const q=state.query.trim().toLowerCase(); return state.dishes.filter(d=>(state.category==='全部'||d.category===state.category)&&(!q||`${d.name} ${d.desc} ${d.category}`.toLowerCase().includes(q))); }
    function renderMenu(){ const html=cats().filter(c=>c!=='全部').map(c=>{ const ds=filtered().filter(d=>d.category===c); if(!ds.length)return''; return `<section><h2 class="section-title">${c}</h2><div class="grid">${ds.map(dishCard).join('')}</div></section>` }).join(''); $('#menu').innerHTML=html||'<div class="panel empty">没有找到匹配菜品</div>'; }
    function dishCard(d){ const off=d.sold_out||d.stock<=0; return `<article class="dish ${off?'sold':''}"><div class="photo">${photo(d)}</div><div class="dishinfo"><div class="dishhead"><div><div class="name">${d.name}</div><div class="meta">${d.category} · 库存 ${Math.max(0,d.stock)}</div></div><div class="price">${money(d.price)}</div></div><p class="desc">${d.desc}</p><div class="opt"><label>规格</label><select id="size-${d.id}" ${off?'disabled':''}><option>标准</option><option>大份</option><option>小份</option></select></div><div class="opt"><label>辣度</label><select id="spicy-${d.id}" ${off?'disabled':''}><option>不辣</option><option>微辣</option><option>中辣</option><option>特辣</option></select></div><div class="opt"><label>忌口</label><div class="checks">${['葱','蒜','香菜'].map(x=>`<label class="check"><input type="checkbox" data-avoid="${d.id}" value="${x}" ${off?'disabled':''}>不要${x}</label>`).join('')}</div></div><div class="actions"><span class="meta">已选 ${qty(d.id)}</span><button class="mini primary" data-add="${d.id}" ${off?'disabled':''}>${off?'已下架':'加入购物车'}</button></div></div></article>` }
    function addCart(id){ const d=state.dishes.find(x=>x.id===id); if(!d||d.sold_out||d.stock<=0)return; if(qty(id)>=d.stock){toast(`${d.name} 库存不足`);return;} const o=selected(id); const item={dish_id:d.id,name:d.name,size:o.size,spicy:o.spicy,avoid:o.avoid,price:price(d,o.size),quantity:1}; const ex=state.cart.find(x=>itemKey(x)===itemKey(item)); if(ex)ex.quantity++; else state.cart.push(item); renderCart(); renderMenu(); }
    function renderCart(){ $('#cartCount').textContent=state.cart.reduce((s,i)=>s+i.quantity,0); $('#total').textContent=money(total()); $('#cartList').innerHTML=state.cart.length?state.cart.map((i,n)=>`<div class="cartitem"><div><strong>${i.name}</strong><small>${i.size} · ${i.spicy}${i.avoid.length?' · '+i.avoid.map(x=>'不要'+x).join('、'):''}</small><small>${money(i.price)} × ${i.quantity}</small><div class="row"><button class="mini" data-line="minus" data-i="${n}">−</button><button class="mini" data-line="plus" data-i="${n}">+</button><button class="mini" data-line="del" data-i="${n}">删除</button></div></div><div class="price">${money(i.price*i.quantity)}</div></div>`).join(''):'<div class="empty">还没有选择菜品<br>请选择规格、口味后加入购物车</div>'; }
    function orderCard(o, merchant){ const cls=o.status==='待出餐'?'warn':o.status==='已完成'?'done':''; return `<article class="card"><div class="cardtop"><div><strong>${o.customer_name}</strong><div class="meta">${o.created_at} · ${o.phone}</div></div><span class="state ${cls}">${o.status}</span></div><div class="meta">${o.items.map(i=>`${i.name} ${i.size}/${i.spicy} x ${i.quantity}`).join('<br>')}${o.note?'<br>备注：'+o.note:''}</div><div class="total"><span>订单金额</span><strong>${money(o.total)}</strong></div>${merchant?`<div class="adminactions"><button class="mini" data-status="已下单" data-order="${o.id}">已下单</button><button class="mini" data-status="待出餐" data-order="${o.id}">待出餐</button><button class="mini primary" data-status="已完成" data-order="${o.id}">已完成</button></div>`:''}</article>`; }
    function renderHistory(){ if(!state.user){$('#history').innerHTML='<div class="empty">登录后显示历史订单</div>';return;} api('/api/orders?phone='+encodeURIComponent(state.user.phone)).then(d=>{$('#history').innerHTML=d.orders.length?d.orders.map(o=>orderCard(o,false)).join(''):'<div class="empty">暂无历史订单</div>';}).catch(e=>$('#history').innerHTML='<div class="empty">'+e.message+'</div>'); }
    function renderOrders(checkNew=true){ api('/api/merchant/orders').then(d=>{ const newOnes=d.orders.filter(o=>!state.seenOrders.has(o.id)); d.orders.forEach(o=>state.seenOrders.add(o.id)); if(checkNew&&newOnes.length) notifyMerchant(newOnes[0]); state.orders=d.orders; $('#orders').innerHTML=d.orders.length?d.orders.map(o=>orderCard(o,true)).join(''):'<div class="empty">暂无订单</div>'; }).catch(e=>$('#orders').innerHTML='<div class="empty">'+e.message+'</div>'); }
    function renderAdminDishes(){ $('#adminDishes').innerHTML=state.dishes.map(d=>`<article class="card"><div class="cardtop"><div class="photo">${photo(d)}</div><div><strong>${d.name}</strong><div class="meta">${d.category} · ${money(d.price)} · 库存 ${d.stock}</div><div class="meta">${d.desc}</div></div><span class="state ${d.sold_out?'warn':'done'}">${d.sold_out?'已下架':'在售'}</span></div><div class="adminactions"><button class="mini" data-dish-act="${d.sold_out?'publish':'unpublish'}" data-dish="${d.id}">${d.sold_out?'上架':'下架'}</button><button class="mini" data-dish-act="image" data-dish="${d.id}">图片</button><button class="mini" data-dish-act="stock" data-dish="${d.id}">库存</button><button class="mini" data-dish-act="price" data-dish="${d.id}">改价</button><button class="mini" data-dish-act="delete" data-dish="${d.id}">删除</button></div></article>`).join(''); }
    function notifyMerchant(o){ if(!state.notify)return; try{ new AudioContext().createOscillator().start(); }catch(e){} if('Notification' in window && Notification.permission==='granted') new Notification('噜噜菜馆新订单', {body:`${o.customer_name} ${money(o.total)}`}); alert(`新订单：${o.customer_name} ${money(o.total)}`); }
    async function loadMenu(){ const d=await api('/api/menu'); state.dishes=d.dishes; renderShell(); }
    $('#loginBtn').onclick=()=>{ const name=$('#loginName').value.trim(), phone=$('#loginPhone').value.trim(); if(!name||!phone){toast('请填写姓名和手机号');return;} state.user={name,phone}; localStorage.setItem('lulu_user',JSON.stringify(state.user)); renderShell(); };
    $('#logoutBtn').onclick=async()=>{ if(state.isAdmin){ await fetch('/api/admin/logout',{method:'POST'}); location.href='/admin'; return; } state.user=null; localStorage.removeItem('lulu_user'); renderShell(); };
    if($('#notifyBtn')) $('#notifyBtn').onclick=async()=>{ state.notify=true; if('Notification' in window && Notification.permission!=='granted') await Notification.requestPermission(); $('#notifyBtn').textContent='商家通知已开启'; };
    $('#merchantTools').onclick=e=>{ const b=e.target.closest('[data-view]'); if(!b)return; document.querySelectorAll('.view').forEach(v=>v.classList.remove('active')); $('#'+b.dataset.view+'View').classList.add('active'); document.querySelectorAll('[data-view]').forEach(x=>x.classList.toggle('active',x===b)); if(b.dataset.view==='merchant') renderOrders(false); };
    $('#tabs').onclick=e=>{ const b=e.target.closest('[data-cat]'); if(b){state.category=b.dataset.cat;renderTabs();renderMenu();} };
    $('#search').oninput=e=>{ state.query=e.target.value; renderMenu(); };
    $('#menu').onclick=e=>{ const b=e.target.closest('[data-add]'); if(b)addCart(Number(b.dataset.add)); };
    $('#cartList').onclick=e=>{ const b=e.target.closest('[data-line]'); if(!b)return; const i=Number(b.dataset.i), item=state.cart[i]; if(!item)return; if(b.dataset.line==='del')state.cart.splice(i,1); if(b.dataset.line==='minus'){item.quantity--; if(item.quantity<=0)state.cart.splice(i,1);} if(b.dataset.line==='plus'){ const d=state.dishes.find(x=>x.id===item.dish_id); if(d&&qty(d.id)<d.stock)item.quantity++; } renderCart(); renderMenu(); };
    $('#clearCart').onclick=()=>{ state.cart=[]; $('#note').value=''; renderCart(); renderMenu(); };
    $('#submit').onclick=async()=>{ if(!state.user){toast('请先登录');return;} if(!state.cart.length){toast('请先选择菜品');return;} const d=await api('/api/orders',{method:'POST',body:JSON.stringify({user:state.user,items:state.cart,note:$('#note').value.trim()})}).catch(e=>({error:e.message})); if(d.error){toast(d.error);return;} state.cart=[]; $('#note').value=''; toast('订单已提交，商家后台已收到通知'); await loadMenu(); renderHistory(); };
    $('#orders').onclick=async e=>{ const b=e.target.closest('[data-status]'); if(!b)return; await api('/api/orders/'+b.dataset.order+'/status',{method:'PATCH',body:JSON.stringify({status:b.dataset.status})}); renderOrders(false); renderHistory(); };
    $('#addDish').onclick=async()=>{ const body={name:$('#dishName').value.trim(),category:$('#dishCategory').value.trim(),price:Number($('#dishPrice').value),desc:$('#dishDesc').value.trim(),image:$('#dishImage').value.trim()}; if(!body.name||!body.category||!body.price){alert('请填写菜名、分类和价格');return;} await api('/api/dishes',{method:'POST',body:JSON.stringify(body)}); $('#dishName').value=$('#dishCategory').value=$('#dishPrice').value=$('#dishDesc').value=$('#dishImage').value=''; loadMenu(); };
    $('#batchPrice').onclick=async()=>{ const delta=Number($('#batchValue').value); if(!delta)return; await api('/api/dishes/batch',{method:'POST',body:JSON.stringify({delta})}); $('#batchValue').value=''; loadMenu(); };
    $('#adminDishes').onclick=async e=>{ const b=e.target.closest('[data-dish-act]'); if(!b)return; const dish=state.dishes.find(d=>d.id===Number(b.dataset.dish)); let body={action:b.dataset.dishAct}; if(body.action==='stock')body.stock=Number(prompt('库存数量',dish?.stock??0)); if(body.action==='price')body.price=Number(prompt('新价格',dish?.price??1)); if(body.action==='image'){ const image=prompt('图片 URL、emoji 或单字',dish?.image||''); if(image===null)return; body.image=image.trim(); } await api('/api/dishes/'+b.dataset.dish,{method:body.action==='delete'?'DELETE':'PATCH',body:JSON.stringify(body)}); loadMenu(); };
    if(state.isAdmin){ document.querySelector('.login').hidden=true; $('#logoutBtn').textContent='退出后台'; $('#userLine').textContent='已进入商家后台'; $('#merchantTools').hidden=false; $('#notifyBtn').hidden=false; document.querySelectorAll('.view').forEach(v=>v.classList.remove('active')); $('#merchantView').classList.add('active'); document.querySelectorAll('[data-view]').forEach(x=>x.classList.toggle('active',x.dataset.view==='merchant')); }
    setInterval(()=>{ if(state.isAdmin && $('#merchantView').classList.contains('active')) renderOrders(true); },3000);
    loadMenu();
  </script>
</body>
</html>"""

ADMIN_LOGIN_HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>噜噜菜馆商家登录</title>
  <link rel="icon" type="image/gif" href="/favicon.gif">
  <link rel="shortcut icon" type="image/gif" href="/favicon.gif">
  <style>
    :root{--bg:#f6f4ee;--panel:#fff;--ink:#20242c;--muted:#6d7683;--line:#dfe3e8;--brand:#0f766e;--accent:#d84b31;--shadow:0 16px 42px rgba(32,36,44,.12)}
    *{box-sizing:border-box}body{min-height:100vh;margin:0;display:grid;place-items:center;color:var(--ink);background:linear-gradient(120deg,rgba(15,118,110,.12),transparent 36%),linear-gradient(300deg,rgba(216,75,49,.11),transparent 32%),var(--bg);font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}.login{width:min(420px,calc(100% - 28px));display:grid;gap:14px;padding:24px;border:1px solid var(--line);border-radius:8px;background:var(--panel);box-shadow:var(--shadow)}h1{margin:0;font-size:32px}.note{margin:0;color:var(--muted);line-height:1.6}.field{min-height:44px;border:1px solid var(--line);border-radius:8px;padding:0 12px;font:inherit}.btn{min-height:44px;border:0;border-radius:8px;color:#fff;background:var(--brand);font:inherit;font-weight:850;cursor:pointer}.toast{min-height:22px;color:var(--accent);font-weight:800}
  </style>
</head>
<body>
  <form class="login" id="loginForm">
    <h1>噜噜菜馆商家后台</h1>
    <p class="note">请输入商家账号密码后进入订单与菜品管理。</p>
    <input class="field" id="username" autocomplete="username" placeholder="账号">
    <input class="field" id="password" type="password" autocomplete="current-password" placeholder="密码">
    <button class="btn" type="submit">登录后台</button>
    <div class="toast" id="toast"></div>
  </form>
  <script>
    document.querySelector('#loginForm').addEventListener('submit', async event => {
      event.preventDefault();
      const username = document.querySelector('#username').value.trim();
      const password = document.querySelector('#password').value;
      const res = await fetch('/api/admin/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username, password})
      });
      if (res.ok) location.href = '/admin';
      else document.querySelector('#toast').textContent = '账号或密码错误';
    });
  </script>
</body>
</html>"""


def admin_page():
    return INDEX_HTML.replace('<body data-admin="0">', '<body data-admin="1">')


def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with db() as con:
        con.execute(
            """CREATE TABLE IF NOT EXISTS dishes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                name TEXT NOT NULL,
                price INTEGER NOT NULL,
                desc TEXT NOT NULL,
                image TEXT NOT NULL,
                stock INTEGER NOT NULL,
                sold_out INTEGER NOT NULL DEFAULT 0
            )"""
        )
        con.execute(
            """CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                table_no TEXT NOT NULL,
                items TEXT NOT NULL,
                total INTEGER NOT NULL,
                note TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )"""
        )
        count = con.execute("SELECT COUNT(*) FROM dishes").fetchone()[0]
        if count == 0:
            con.executemany(
                "INSERT INTO dishes(category,name,price,desc,image,stock,sold_out) VALUES(?,?,?,?,?,?,?)",
                DEFAULT_DISHES,
            )


def rows_to_dishes(rows):
    return [
        {
            "id": r["id"],
            "category": r["category"],
            "name": r["name"],
            "price": r["price"],
            "desc": r["desc"],
            "image": r["image"],
            "stock": r["stock"],
            "sold_out": bool(r["sold_out"]),
        }
        for r in rows
    ]


def row_to_order(r):
    return {
        "id": r["id"],
        "customer_name": r["customer_name"],
        "phone": r["phone"],
        "items": json.loads(r["items"]),
        "total": r["total"],
        "note": r["note"] or "",
        "status": r["status"],
        "created_at": r["created_at"],
    }


class Handler(BaseHTTPRequestHandler):
    def admin_token(self):
      cookie = self.headers.get("Cookie") or ""
      for part in cookie.split(";"):
          key, _, value = part.strip().partition("=")
          if key == "lulu_admin":
              return value
      return ""

    def is_admin(self):
        return self.admin_token() in ADMIN_SESSIONS

    def require_admin(self):
        if self.is_admin():
            return True
        self.send_json({"error": "请先登录商家后台"}, 401)
        return False

    def send_html(self, html):
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_head_ok(self, content_type="text/html; charset=utf-8", length=0):
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.end_headers()

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_HEAD(self):
        parsed = urlparse(self.path)
        if parsed.path in ["/", "/admin"]:
            self.send_head_ok(length=len(INDEX_HTML.encode("utf-8")))
            return
        if parsed.path == "/favicon.gif" and FAVICON.exists():
            self.send_head_ok("image/gif", FAVICON.stat().st_size)
            return
        if parsed.path.startswith("/api/"):
            self.send_head_ok("application/json; charset=utf-8", 0)
            return
        self.send_response(404)
        self.end_headers()

    def read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.send_html(INDEX_HTML)
            return
        if parsed.path == "/admin":
            self.send_html(admin_page() if self.is_admin() else ADMIN_LOGIN_HTML)
            return
        if parsed.path == "/favicon.gif" and FAVICON.exists():
            body = FAVICON.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "image/gif")
            self.send_header("Cache-Control", "public, max-age=86400")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if parsed.path == "/api/menu":
            with db() as con:
                rows = con.execute("SELECT * FROM dishes ORDER BY id").fetchall()
            self.send_json({"dishes": rows_to_dishes(rows)})
            return
        if parsed.path == "/api/orders":
            phone = parse_qs(parsed.query).get("phone", [""])[0]
            with db() as con:
                rows = con.execute("SELECT * FROM orders WHERE phone=? ORDER BY id DESC", (phone,)).fetchall()
            self.send_json({"orders": [row_to_order(r) for r in rows]})
            return
        if parsed.path == "/api/merchant/orders":
            if not self.require_admin():
                return
            with db() as con:
                rows = con.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 100").fetchall()
            self.send_json({"orders": [row_to_order(r) for r in rows]})
            return
        self.send_json({"error": "not found"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        data = self.read_json()
        if parsed.path == "/api/admin/login":
            if data.get("username") == ADMIN_USER and data.get("password") == ADMIN_PASSWORD:
                token = secrets.token_urlsafe(32)
                ADMIN_SESSIONS.add(token)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Set-Cookie", f"lulu_admin={token}; Path=/; HttpOnly; SameSite=Lax")
                body = json.dumps({"ok": True}).encode("utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            self.send_json({"error": "账号或密码错误"}, 401)
            return
        if parsed.path == "/api/admin/logout":
            token = self.admin_token()
            if token in ADMIN_SESSIONS:
                ADMIN_SESSIONS.remove(token)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Set-Cookie", "lulu_admin=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax")
            body = json.dumps({"ok": True}).encode("utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if parsed.path == "/api/orders":
            user = data.get("user") or {}
            items = data.get("items") or []
            if not user.get("name") or not user.get("phone"):
                self.send_json({"error": "请先登录"}, 400)
                return
            if not items:
                self.send_json({"error": "购物车为空"}, 400)
                return
            with db() as con:
                dishes = {r["id"]: r for r in con.execute("SELECT * FROM dishes").fetchall()}
                total = 0
                for item in items:
                    dish = dishes.get(int(item["dish_id"]))
                    if not dish or dish["sold_out"] or dish["stock"] < int(item["quantity"]):
                        self.send_json({"error": f"{item.get('name', '菜品')} 库存不足"}, 400)
                        return
                    total += int(item["price"]) * int(item["quantity"])
                for item in items:
                    con.execute(
                        "UPDATE dishes SET stock=stock-?, sold_out=CASE WHEN stock-?<=0 THEN 1 ELSE sold_out END WHERE id=?",
                        (int(item["quantity"]), int(item["quantity"]), int(item["dish_id"])),
                    )
                cur = con.execute(
                    "INSERT INTO orders(customer_name,phone,table_no,items,total,note,status,created_at) VALUES(?,?,?,?,?,?,?,?)",
                    (
                        user["name"],
                        user["phone"],
                        "",
                        json.dumps(items, ensure_ascii=False),
                        total,
                        data.get("note") or "",
                        "已下单",
                        time.strftime("%Y-%m-%d %H:%M:%S"),
                    ),
                )
            self.send_json({"ok": True, "order_id": cur.lastrowid})
            return
        if parsed.path == "/api/dishes":
            if not self.require_admin():
                return
            if not data.get("name") or not data.get("category") or not data.get("price"):
                self.send_json({"error": "菜名、分类、价格必填"}, 400)
                return
            with db() as con:
                con.execute(
                    "INSERT INTO dishes(category,name,price,desc,image,stock,sold_out) VALUES(?,?,?,?,?,?,0)",
                    (
                        data["category"],
                        data["name"],
                        int(data["price"]),
                        data.get("desc") or "新品上架，欢迎品尝。",
                        data.get("image") or data["name"][0],
                        int(data.get("stock") or 20),
                    ),
                )
            self.send_json({"ok": True})
            return
        if parsed.path == "/api/dishes/batch":
            if not self.require_admin():
                return
            delta = int(data.get("delta") or 0)
            with db() as con:
                con.execute("UPDATE dishes SET price=MAX(1, price + ?)", (delta,))
            self.send_json({"ok": True})
            return
        self.send_json({"error": "not found"}, 404)

    def do_PATCH(self):
        parsed = urlparse(self.path)
        data = self.read_json()
        parts = parsed.path.strip("/").split("/")
        if len(parts) == 4 and parts[:2] == ["api", "orders"] and parts[3] == "status":
            if not self.require_admin():
                return
            status = data.get("status")
            if status not in ["已下单", "待出餐", "已完成"]:
                self.send_json({"error": "状态无效"}, 400)
                return
            with db() as con:
                con.execute("UPDATE orders SET status=? WHERE id=?", (status, int(parts[2])))
            self.send_json({"ok": True})
            return
        if len(parts) == 3 and parts[:2] == ["api", "dishes"]:
            if not self.require_admin():
                return
            dish_id = int(parts[2])
            action = data.get("action")
            with db() as con:
                if action == "toggle":
                    con.execute("UPDATE dishes SET sold_out=CASE sold_out WHEN 1 THEN 0 ELSE 1 END WHERE id=?", (dish_id,))
                elif action == "publish":
                    con.execute("UPDATE dishes SET sold_out=0 WHERE id=?", (dish_id,))
                elif action == "unpublish":
                    con.execute("UPDATE dishes SET sold_out=1 WHERE id=?", (dish_id,))
                elif action == "image":
                    image = (data.get("image") or "").strip()
                    if not image:
                        self.send_json({"error": "图片不能为空"}, 400)
                        return
                    con.execute("UPDATE dishes SET image=? WHERE id=?", (image, dish_id))
                elif action == "stock":
                    stock = max(0, int(data.get("stock") or 0))
                    con.execute("UPDATE dishes SET stock=?, sold_out=? WHERE id=?", (stock, 1 if stock == 0 else 0, dish_id))
                elif action == "price":
                    con.execute("UPDATE dishes SET price=? WHERE id=?", (max(1, int(data.get("price") or 1)), dish_id))
                else:
                    self.send_json({"error": "操作无效"}, 400)
                    return
            self.send_json({"ok": True})
            return
        self.send_json({"error": "not found"}, 404)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        parts = parsed.path.strip("/").split("/")
        if len(parts) == 3 and parts[:2] == ["api", "dishes"]:
            if not self.require_admin():
                return
            with db() as con:
                con.execute("DELETE FROM dishes WHERE id=?", (int(parts[2]),))
            self.send_json({"ok": True})
            return
        self.send_json({"error": "not found"}, 404)

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args))


if __name__ == "__main__":
    init_db()
    print(f"噜噜菜馆服务启动：http://{HOST}:{PORT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
