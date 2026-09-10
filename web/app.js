const $ = (id) => document.getElementById(id);
fetch('/readyz').then((response) => response.json()).then((data) => {
  if (!data.llm_mode) {
    const option = $('mode').querySelector('option[value="llm"]');
    option.disabled = true;
    option.textContent = 'LLM mode · configure OPENAI_API_KEY';
  }
}).catch(() => {});
$('analyze').addEventListener('click', async () => {
  const button = $('analyze'); button.disabled = true; button.firstChild.textContent = 'Analyzing… ';
  $('error').textContent = '';
  try {
    const response = await fetch('/v1/analyze', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({message:$('message').value, mode:$('mode').value})});
    const data = await response.json(); if(!response.ok) throw new Error(data.detail || 'Analysis failed');
    $('results').classList.remove('hidden');
    $('intent').textContent = data.classification.intent.replaceAll('_',' ');
    const pct = Math.round(data.classification.confidence*100); $('confidence').textContent = `${pct}% confidence · ${data.classification.rationale}`; $('confidence-bar').style.width = `${pct}%`;
    $('route').textContent = data.routing.action.replace('_',' '); $('reason').textContent = data.routing.reason;
    $('draft').textContent = data.draft.text; $('grounding').textContent = data.draft.grounded ? `Grounded · ${data.draft.exemplar_ids.length} precedents` : 'Ungrounded · human review';
    $('evidence').innerHTML = data.retrieved.length ? data.retrieved.map((x,i)=>`<div class="evidence-item"><small>${String(i+1).padStart(2,'0')} · ${Math.round(x.similarity*100)}% similarity · ${escapeHtml(x.thread_id)}</small><p>${escapeHtml(x.customer_message)}</p><strong>${escapeHtml(x.brand_reply)}</strong></div>`).join('') : '<p>No relevant precedent found.</p>';
    $('latency').textContent = `${data.latency_ms} ms · ${data.mode} mode`; $('results').scrollIntoView({behavior:'smooth',block:'start'});
  } catch(error) { $('error').textContent = error.message; }
  finally { button.disabled=false; button.firstChild.textContent='Analyze message '; }
});
function escapeHtml(value){ const node=document.createElement('div'); node.textContent=value; return node.innerHTML; }
