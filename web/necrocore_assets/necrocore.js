'use strict';
function updateBulkUI(){
 const items=Array.from(document.querySelectorAll('.row-check'));
 const chosen=items.filter(x=>x.checked);
 const count=document.getElementById('selected-count');if(count)count.textContent=chosen.length+' selected';
 const all=document.getElementById('select-all');if(all){all.checked=items.length>0&&chosen.length===items.length;all.indeterminate=chosen.length>0&&chosen.length<items.length;}
 items.forEach(x=>{const tr=x.closest('tr');if(tr)tr.classList.toggle('marked',x.checked);});
}
async function loadAndCopy(url,button){
 const old=button?button.textContent:'';
 try{if(button){button.disabled=true;button.textContent='Preparing…'}
 const resp=await fetch(url,{cache:'no-store'});if(!resp.ok)throw Error('HTTP '+resp.status);
 copyText(await resp.text());}
 catch(e){alert('Unable to prepare report: '+e.message)}
 finally{if(button){button.disabled=false;button.textContent=old;}}
}
function copyText(text){
 let box=document.getElementById('chatgpt-export');
 if(!box){
  const section=document.createElement('section');section.className='card';
  section.innerHTML='<h2>Report prepared for ChatGPT</h2><p>If your browser blocks automatic clipboard access, select the contents below and press Ctrl+C.</p>';
  box=document.createElement('textarea');box.id='chatgpt-export';box.className='export-text';box.readOnly=true;
  section.append(box);(document.getElementById('export-target')||document.querySelector('main')||document.body).prepend(section);
 }
 box.value=text;box.focus();box.select();let copied=false;
 try{copied=document.execCommand('copy')}catch(_){/* HTTP clipboard restrictions */}
 const f=document.getElementById('copy-feedback');if(f)f.textContent=copied?'Copied; paste into ChatGPT.':'Text selected; press Ctrl+C to copy.';
 if(!copied)box.scrollIntoView({behavior:'smooth',block:'center'});
}
function copyCurrentReport(){let el=document.getElementById('chatgpt-export');if(el)copyText(el.value);}
function showEasternDates(){
 document.querySelectorAll('time[data-utc]').forEach(node=>{
  const raw=node.dataset.utc||'';
  if(!/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(raw))return;
  const d=new Date(raw.replace(' ','T')+'Z');if(!Number.isFinite(d.getTime()))return;
  node.textContent=new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',timeZoneName:'short',month:'short',day:'numeric',year:'numeric',hour:'numeric',minute:'2-digit'}).format(d);
  node.title='Stored: '+raw+' UTC';
 });
}
document.addEventListener('DOMContentLoaded',()=>{
 showEasternDates();
 const u=new URLSearchParams(window.location.search);const kind=u.get('kind')||'Bug';
 const isClosed=u.get('status')==='Closed';
 const nav=isClosed?'Closed':(u.get('kind')?kind:'home');
 document.querySelectorAll('[data-nav]').forEach(a=>a.classList.toggle('active',a.dataset.nav===nav));
 const all=document.getElementById('select-all');const checks=document.querySelectorAll('.row-check');
 if(all)all.addEventListener('change',()=>{checks.forEach(c=>c.checked=all.checked);updateBulkUI()});
 checks.forEach(c=>c.addEventListener('change',updateBulkUI));updateBulkUI();
 const form=document.getElementById('bulk-form');
 if(form)form.addEventListener('submit',e=>{
   const count=document.querySelectorAll('.row-check:checked').length;
   if(!count){e.preventDefault();alert('Select at least one report first.');return;}
   const action=e.submitter?.value||'';
   if(action==='delete'){
     if(!confirm('Permanently delete '+count+' selected report(s)? This cannot be undone from the dashboard.')){e.preventDefault();return;}
     const flag=document.getElementById('confirm-delete');if(flag)flag.value='YES';
   }
 });
});
