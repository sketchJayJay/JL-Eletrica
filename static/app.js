
function toggleSidebar(){
  const sidebar=document.querySelector('.sidebar');
  const backdrop=document.querySelector('.sidebar-backdrop');
  sidebar?.classList.toggle('open');
  backdrop?.classList.toggle('show');
  document.body.classList.toggle('menu-open');
}
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

// close sidebar when clicking nav on mobile
document.addEventListener('click', (e)=>{
  const a=e.target.closest('.sidebar .nav a');
  if(a && window.innerWidth<=980){
    document.querySelector('.sidebar')?.classList.remove('open');
    document.querySelector('.sidebar-backdrop')?.classList.remove('show');
    document.body.classList.remove('menu-open');
  }
});


async function shareOrderPdf(pdfUrl, fileName){
  const btn = document.activeElement;
  const oldText = btn && btn.innerHTML;
  try{
    if(btn) btn.classList.add('is-loading');
    const response = await fetch(pdfUrl, {credentials:'same-origin'});
    if(!response.ok) throw new Error('Não foi possível gerar o PDF.');
    const blob = await response.blob();
    const file = new File([blob], fileName, {type:'application/pdf'});

    if(navigator.share && (!navigator.canShare || navigator.canShare({files:[file]}))){
      await navigator.share({
        title:'Ordem de Serviço - JL Elétrica',
        text:'Segue a Ordem de Serviço da JL Elétrica Automotiva.',
        files:[file]
      });
      return;
    }

    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = fileName; document.body.appendChild(a); a.click(); a.remove();
    setTimeout(()=>URL.revokeObjectURL(url), 1500);
    alert('O PDF foi baixado. Neste navegador o envio de arquivo direto não é suportado; anexe o PDF no WhatsApp.');
  }catch(err){
    if(err && err.name === 'AbortError') return;
    alert(err?.message || 'Não foi possível compartilhar a OS em PDF.');
  }finally{
    if(btn) btn.classList.remove('is-loading');
  }
}
