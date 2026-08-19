
function toggleSidebar(){document.querySelector('.sidebar')?.classList.toggle('open')}
function confirmDelete(msg='Deseja realmente excluir este registro?'){return confirm(msg)}
function moneyBR(v){return Number(v||0).toLocaleString('pt-BR',{style:'currency',currency:'BRL'})}

function addItemRow(){
  const box=document.getElementById('items-box'); if(!box)return;
  const row=document.createElement('div'); row.className='item-row';
  row.innerHTML=`
    <div class="field"><input name="item_desc[]" placeholder="Descrição do serviço/material" required></div>
    <div class="field"><input name="item_qty[]" type="number" step="0.01" min="0" value="1" oninput="calcTotal()"></div>
    <div class="field"><input name="item_price[]" type="number" step="0.01" min="0" value="0" oninput="calcTotal()"></div>
    <button type="button" class="btn btn-danger btn-sm" onclick="this.parentElement.remove();calcTotal()">×</button>`;
  box.appendChild(row); calcTotal();
}
function calcTotal(){
  const qs=[...document.querySelectorAll('input[name="item_qty[]"]')];
  const ps=[...document.querySelectorAll('input[name="item_price[]"]')];
  let t=0; qs.forEach((q,i)=>t+=(parseFloat(q.value)||0)*(parseFloat(ps[i]?.value)||0));
  const el=document.getElementById('total-preview'); if(el)el.textContent=moneyBR(t);
}
document.addEventListener('DOMContentLoaded',calcTotal);

function filterSelect(input, selectId){
  const term=(input.value||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'');
  const sel=document.getElementById(selectId); if(!sel)return;
  [...sel.options].forEach((opt,i)=>{
    if(i===0){opt.hidden=false;return}
    const txt=(opt.textContent||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'');
    opt.hidden=term && !txt.includes(term);
  });
}
