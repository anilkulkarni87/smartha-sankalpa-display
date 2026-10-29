'use strict';
const $ = id => document.getElementById(id);
let defaults={}, actions={}, fullTemplates={}, familyTemplates={};
let variations=[], familyOverride=null, editing=null, wordingBusy=false;
let hiddenVariations=[];
const modeNames = {morning:'Morning', noon:'Noon', evening:'Evening'};
let storageAvailable=true;
function read(key){try{return localStorage.getItem('sankalpa-'+key)}catch{storageAvailable=false;return null}}
function save(key,value){try{localStorage.setItem('sankalpa-'+key,value)}catch{storageAvailable=false}}
const params = new URLSearchParams(location.search);
let catalogue=[], selected=null, data=null, requestNumber=0, activeRequest=null, lastSuccess=null, loadFailed=false;
let mode=read('mode')||'morning';
if(!modeNames[mode])mode='morning';
$('lang').value=['roman','sanskrit','kannada'].includes(read('lang'))?read('lang'):'roman';
$('form').value='family';
$('gotra').value=read('gotra')||'';
$('scale').value=read('scale')||30;
$('timeMode').value=read('timeMode')==='sunrise'?'sunrise':'now';
const conventionControls={sunriseMode:['hindu','apparent'],rituMode:['solar','lunar'],yearMode:['conjunction','sunrise']};
for(const [id,options] of Object.entries(conventionControls))$(id).value=options.includes(read(id))?read(id):options[0];
function savedTemplate(lang){return read('template-'+lang)||((read('lang')||'roman')===lang?read('template'):null)||defaults[lang]}
function familyUS(){return $('form').value==='family'&&selected?.country==='United States'}
function validTemplates(value){return value&&['roman','sanskrit','kannada'].every(key=>typeof value[key]==='string'&&value[key].trim()&&value[key].length<=20000)}
async function loadWordings(){
 try{
  const stored=JSON.parse(read('wordings')||'null');
  if(stored?.version===1){
   familyOverride=validTemplates(stored.family)?stored.family:null;
   variations=Array.isArray(stored.variations)?stored.variations.filter(v=>typeof v.id==='string'&&v.id!=='family'&&typeof v.name==='string'&&typeof v.country==='string'&&validTemplates(v.templates)):[];
   hiddenVariations=Array.isArray(stored.hidden)?stored.hidden.filter(v=>typeof v.id==='string'&&typeof v.name==='string'&&typeof v.country==='string'&&validTemplates(v.templates)):[];
  }
 }catch{ $('wordingStatus').textContent='Saved variations could not be read. Your supplied wording is still available.'; }
 // Preserve old custom templates as a named variation, without overwriting them.
 if(!read('wordings')){
  const scripts=['roman','sanskrit','kannada'];
  const preferred=scripts.includes(read('lang'))?read('lang'):'roman';
  const script=read('template-'+preferred)||read('template')?preferred:scripts.find(key=>read('template-'+key));
  const text=script&&(read('template-'+script)||read('template'));
  if(text){
   try{
    const response=await fetch('/api/template-formats',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text,script}),signal:AbortSignal.timeout(15000)});
    if(!response.ok)throw Error('Legacy wording could not be converted');
    const result=await response.json();
    variations.push({id:'legacy-custom',name:'Previously saved wording',country:selected.country,templates:result.templates});
   }catch{$('status').textContent='Previously saved custom text is preserved in browser storage, but could not be loaded.'}
  }
 }
 refreshWordings(read('form'));
 $('wordingUndo').classList.toggle('hide',!hiddenVariations.length);
}
function refreshWordings(wanted=$('form').value){
 $('form').replaceChildren(new Option('My family Sankalpa','family'));
 for(const variation of variations)$('form').add(new Option(variation.name,variation.id));
 $('form').value=variations.some(v=>v.id===wanted)?wanted:'family';
}
function chosenTemplate(){
 const script=$('lang').value;
 if($('form').value==='family')return familyUS()?(familyOverride||familyTemplates)[script]:fullTemplates[script];
 const variation=variations.find(v=>v.id===$('form').value);
 return variation?.country===selected?.country?variation.templates[script]:fullTemplates[script];
}
function closeWording(){
 editing=null;$('wordingEditor').classList.add('hide');$('lang').disabled=false;$('form').disabled=false;
 $('template').value=chosenTemplate();render();
}
function openWording(add=false){
 if(!selected||wordingBusy)return;
 const current=variations.find(v=>v.id===$('form').value);
 const id=add?'variation-'+crypto.randomUUID():$('form').value;
 editing={id,country:current?.country||selected.country,script:$('lang').value};
 // Outside the US, edits to the fallback become a separate local variation.
 if((id==='family'&&!familyUS())||(current&&current.country!==selected.country)){editing.id='variation-'+crypto.randomUUID();editing.country=selected.country;}
 $('variationName').value=add?'New variation':current?.name||'My family Sankalpa';
 $('variationName').disabled=editing.id==='family';
 $('archiveWording').classList.toggle('hide',!current||current.id!==editing.id);
 $('editorHeading').textContent=add?'Add a variation':'Edit your wording';
 $('editorScope').textContent='Editing '+$('lang').selectedOptions[0].textContent+' · Applies in '+editing.country+'.';
 $('template').value=chosenTemplate();$('wordingStatus').textContent='';
 $('wordingEditor').classList.remove('hide');$('lang').disabled=true;$('form').disabled=true;
 $('wordingEditor').scrollIntoView({behavior:'smooth',block:'start'});
}
$('editWording').onclick=()=>openWording();
$('addVariation').onclick=()=>openWording(true);
$('cancelWording').onclick=()=>{if(!wordingBusy)closeWording()};
$('archiveWording').onclick=()=>{
 if(wordingBusy||!editing)return;
 const current=variations.find(v=>v.id===editing.id);if(!current)return;
 const next=variations.filter(v=>v.id!==editing.id),hidden=[...hiddenVariations,current];
 try{localStorage.setItem('sankalpa-wordings',JSON.stringify({version:1,family:familyOverride,variations:next,hidden}));
  variations=next;hiddenVariations=hidden;refreshWordings('family');save('form','family');closeWording();
  $('wordingUndo').classList.remove('hide');
 }catch{$('wordingStatus').textContent='Could not hide the variation; browser storage is unavailable.'}
};
$('wordingUndo').onclick=()=>{
 if(wordingBusy||!hiddenVariations.length)return;
 const restored=hiddenVariations.at(-1),hidden=hiddenVariations.slice(0,-1),next=[...variations,restored];
 try{localStorage.setItem('sankalpa-wordings',JSON.stringify({version:1,family:familyOverride,variations:next,hidden}));
  variations=next;hiddenVariations=hidden;refreshWordings(restored.id);save('form',restored.id);$('template').value=chosenTemplate();render();
  $('wordingUndo').classList.toggle('hide',!hidden.length);
 }catch{$('status').textContent='Could not restore the variation; browser storage is unavailable.'}
};
$('saveWording').onclick=async()=>{
 if(!editing||wordingBusy)return;
 const name=$('variationName').value.trim();
 if(!name){$('wordingStatus').textContent='Give this wording a name.';return}
 wordingBusy=true;$('saveWording').disabled=true;$('cancelWording').disabled=true;$('reset').disabled=true;
 for(const id of ['country','city','editWording','addVariation','archiveWording','template','variationName'])$(id).disabled=true;
 try{
  const response=await fetch('/api/template-formats',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:$('template').value,script:editing.script}),signal:AbortSignal.timeout(15000)});
  const result=await response.json();
  if(!response.ok)throw Error(result.detail||'Could not save wording');
  const nextFamily=editing.id==='family'?result.templates:familyOverride;
  const nextVariations=editing.id==='family'?variations:[...variations.filter(v=>v.id!==editing.id),{id:editing.id,name,country:editing.country,templates:result.templates}];
  // Commit only after browser storage succeeds; failed saves leave the draft open.
  localStorage.setItem('sankalpa-wordings',JSON.stringify({version:1,family:nextFamily,variations:nextVariations,hidden:hiddenVariations}));
  familyOverride=nextFamily;variations=nextVariations;refreshWordings(editing.id);save('form',editing.id);closeWording();
  $('readerTitle').scrollIntoView({behavior:'smooth',block:'start'});
 }catch(error){$('wordingStatus').textContent='Not saved: '+(error.name==='TimeoutError'?'The local server timed out. Your draft is still here.':error.message)}
 finally{wordingBusy=false;for(const id of ['saveWording','cancelWording','reset','country','city','editWording','addVariation','archiveWording','template','variationName'])$(id).disabled=false}
};
function timezone(){return selected?.timezone||'America/Los_Angeles'}
function displayDate(s){return s?new Date(s).toLocaleString('en-US',{timeZone:timezone(),month:'short',day:'numeric',hour:'numeric',minute:'2-digit'}):'—'}
function clock(){
 $('clock').textContent=new Date().toLocaleString('en-US',{timeZone:timezone(),dateStyle:'full',timeStyle:'short'});
 if(lastSuccess){
  const age=Math.floor((Date.now()-lastSuccess)/1000);
  $('status').textContent=(loadFailed||age>120?'Updates interrupted · ':'')+'Last successful refresh '+displayDate(new Date(lastSuccess).toISOString())+' · Updates every minute'+(!storageAvailable?' · Browser storage unavailable; settings will not survive a reload.':'');
 }
}
function notice(message,error=false){$('notice').textContent=message;$('notice').classList.toggle('error',error)}
function renderRecital(template,values){
 const highlights={samvatsara:['calendar','Samvatsara'],recital_samvatsara:['calendar','Samvatsara'],
  ayana:['calendar','Ayana'],recital_ayana:['calendar','Ayana'],
  ritu:['calendar','Ritu'],recital_ritu:['calendar','Ritu'],
  masa:['calendar','Month'],recital_masa:['calendar','Month'],family_masa:['calendar','Month'],
  paksha:['calendar','Paksha'],recital_paksha:['calendar','Paksha'],
  yoga:['calendar','Yoga'],recital_yoga:['calendar','Yoga'],
  karana:['calendar','Karana'],recital_karana:['calendar','Karana'],
  tithi:['tithi','Tithi'],recital_tithi:['tithi','Tithi'],family_tithi:['tithi','Tithi'],
  vara:['vara','Vaara'],recital_vara:['vara','Vaara'],family_vara:['vara','Vaara'],
  nakshatra:['nakshatra','Nakshatra'],recital_nakshatra:['nakshatra','Nakshatra']};
 const fragment=document.createDocumentFragment();let cursor=0;
 for(const match of template.matchAll(/\{(\w+)\}/g)){
  fragment.append(document.createTextNode(template.slice(cursor,match.index)));
  const key=match[1],value=values[key]||'['+key+' — please set]';
  if(highlights[key]&&values[key]){
   const span=document.createElement('span');
   span.className='recital-field recital-'+highlights[key][0];
   span.title=highlights[key][1];span.textContent=value;fragment.append(span);
  }else fragment.append(document.createTextNode(value));
  cursor=match.index+match[0].length;
 }
 fragment.append(document.createTextNode(template.slice(cursor)));
 $('sankalpa').replaceChildren(fragment);
}
function syncMode(){document.querySelectorAll('[data-mode]').forEach(button=>{const on=button.dataset.mode===mode;button.classList.toggle('selected',on);button.setAttribute('aria-pressed',String(on))})}
function render(){
 syncMode();
 $('readerTitle').textContent='Yajurveda · '+modeNames[mode]+' Sankalpa';
 if(!data)return;
 $('calendarSummary').textContent=data.samvatsara+' · '+data.ayana+' · '+data.ritu+' · '+data.masa_display+' masa';
 const fields=[['ಸಂವತ್ಸರ · Samvatsara','samvatsara',true],['ಅಯನ · Ayana','ayana',true],['ಋತು · Ritu','ritu',true],['ಮಾಸ · Masa','masa_display',true],['ಪಕ್ಷ · Paksha','paksha'],['ತಿಥಿ · Tithi','tithi'],['ವಾರ · Vara','vara'],['ನಕ್ಷತ್ರ · Nakshatra','nakshatra'],['ಯೋಗ · Yoga','yoga',true],['ಕರಣ · Karana','karana',true],['ಸೂರ್ಯೋದಯ · Sunrise','sunrise',true]];
 $('grid').replaceChildren();
 for(const [label,key,secondary] of fields){
  const cell=document.createElement('div');cell.className='cell'+(secondary?' secondary':'');
  const small=document.createElement('small');small.textContent=label;cell.append(small);
  const strong=document.createElement('strong');strong.textContent=key==='sunrise'?displayDate(data[key]):data[key];cell.append(strong);
  if(key==='vara'){
   const note=document.createElement('em');
   const civilDay=new Date(data.timestamp).toLocaleDateString('en-US',{timeZone:data.timezone,weekday:'long'});
   note.textContent=civilDay+' · Local calendar weekday; changes at midnight.';
   cell.append(note);
  }
  if(data[key+'_ends']){const end=document.createElement('em');end.textContent='Changes '+displayDate(data[key+'_ends']);cell.append(end)}
  $('grid').append(cell);
 }
 const values={...data,masa:data.masa_display,...(data.recital?.[$('lang').value]||{}),...(data.family_recital?.[$('lang').value]||{}),gotra:$('gotra').value,sandhya_action:actions[$('lang').value][mode]};
 if(data.review_required)$('sankalpa').textContent='Calendar recital withheld: Kshaya month detected. Confirm the month wording with your trusted Panchanga or teacher.';
 else renderRecital(editing?$('template').value:chosenTemplate(),values);
 $('sankalpa').style.fontSize=$('scale').value+'px';
 $('sankalpa').lang={roman:'sa-Latn',sanskrit:'sa',kannada:'sa-Knda'}[$('lang').value];
 syncAudioText();
 const atSunrise=$('timeMode').value==='sunrise';
 const scopedVariation=variations.find(v=>v.id===$('form').value);
 if(!loadFailed)notice((data.warnings.length?data.warnings.join(' ')+' · ':'')+(atSunrise?'Sunrise reference':'Current Panchanga')+' · '+displayDate(data.timestamp)+' · '+data.location+' · '+data.timezone,data.review_required);
 $('calculationProfile').textContent='Amanta · Lahiri · Ayana: sidereal Makara/Karka. Lunar month: '+displayDate(data.lunar_month_start)+' to '+displayDate(data.lunar_month_end)+'. This year’s selected turnover: '+displayDate(data.year_boundary)+'.';
 $('readerNote').textContent=(familyUS()?'Your family wording for US locations, with the existing opening and session closing. ':scopedVariation&&scopedVariation.country===selected.country?'Your saved variation: '+scopedVariation.name+'. ':'Standard geography is used here; the selected wording is saved for '+(scopedVariation?.country||'United States')+'. ')+(editing?'Unsaved preview. ':'')+'Calendar fields update automatically. Teacher review is pending. '+(atSunrise?'Showing today’s sunrise reference.':'Values apply to the displayed moment.');
}
async function getJSON(url,signal){
 const response=await fetch(url,{signal:signal||AbortSignal.timeout(15000),cache:'no-store'});
 if(!response.ok)throw Error('HTTP '+response.status);
 return response.json();
}
async function load(){
 if(!selected)return;
 const number=++requestNumber, city=selected.id;
 activeRequest?.abort();activeRequest=new AbortController();
 const controller=activeRequest, timer=setTimeout(()=>controller.abort(),15000);
 notice('Updating '+selected.city+'…');
 try{
  const query=new URLSearchParams({city,sunrise_mode:$('sunriseMode').value,ritu_mode:$('rituMode').value,year_mode:$('yearMode').value});
  const url='/api/panchanga?'+query;
  let result=await getJSON(url,controller.signal);
  if($('timeMode').value==='sunrise')result=await getJSON(url+'&at='+encodeURIComponent(result.sunrise),controller.signal);
  if(number!==requestNumber)return;
  if(result.city_id!==city||!result.timestamp||!result.tithi)throw Error('Incomplete calendar response');
  data=result;lastSuccess=Date.now();loadFailed=false;render();clock();
 }catch(error){
  if(number!==requestNumber)return;
  loadFailed=true;
  notice('Cannot update '+selected.city+': '+(error.name==='AbortError'?'request timed out':error.message)+'. '+(data?'Values below are from the last successful update. ':'')+'Check the server, then choose Refresh now.',true);
  clock();
 }finally{clearTimeout(timer)}
}
function populateCities(country,preferred){
 $('city').replaceChildren();
 catalogue.filter(item=>item.country===country).forEach(item=>$('city').add(new Option(item.city,item.id)));
 if(catalogue.some(item=>item.country===country&&item.id===preferred))$('city').value=preferred;
}
function chooseCity(){
 selected=catalogue.find(item=>item.id===$('city').value);
 if(editing)closeWording();
 $('template').value=chosenTemplate();
 save('city',selected.id);
 data=null;lastSuccess=null;loadFailed=false;$('grid').replaceChildren();$('sankalpa').textContent='Loading Sankalpa…';$('status').textContent='';syncAudioText();
 $('locationTitle').textContent='Smartha · Yajurveda · '+selected.city+', '+selected.country+' · '+selected.timezone;
 $('coordinates').textContent=selected.latitude+'°, '+selected.longitude+'° (city centre)';
 document.title='Sankalpa · '+selected.city;
 clock();load();
}
async function initialise(){
 try{
  const [locationsResult,formats]=await Promise.all([getJSON('/api/locations'),getJSON('/api/text-formats')]);
  catalogue=locationsResult;defaults=formats.templates;actions=formats.actions;fullTemplates=formats.full_templates;familyTemplates=formats.family_templates;
  $('template').value=chosenTemplate();$('lang').disabled=false;
  if(!Array.isArray(catalogue)||!catalogue.length)throw Error('Location list unavailable');
  $('country').replaceChildren();
  [...new Set(catalogue.map(item=>item.country))].sort().forEach(country=>$('country').add(new Option(country,country)));
  const wanted=params.get('city')||read('city')||'bellevue';
  const first=catalogue.find(item=>item.id===wanted)||catalogue.find(item=>item.id==='bellevue')||catalogue[0];
  $('country').value=first.country;populateCities(first.country,first.id);
  $('country').disabled=false;$('city').disabled=false;selected=first;await loadWordings();chooseCity();
 }catch(error){notice('Cannot load locations: '+error.message+'. Check that the server is running and choose Refresh now.',true)}
}
$('country').onchange=()=>{populateCities($('country').value);chooseCity()};
$('city').onchange=chooseCity;
document.querySelectorAll('[data-mode]').forEach(button=>button.onclick=()=>{mode=button.dataset.mode;save('mode',mode);render()});
$('refresh').onclick=()=>selected?load():initialise();
$('toggle').onclick=()=>$('settings').classList.toggle('hide');
$('print').onclick=()=>window.print();
$('lang').onchange=()=>{$('template').value=chosenTemplate();save('lang',$('lang').value);render()};
$('form').onchange=()=>{$('template').value=chosenTemplate();save('form',$('form').value);render()};
$('template').oninput=render;
$('insertToken').onclick=()=>{if(!editing||wordingBusy)return;const editor=$('template');editor.setRangeText('{'+$('insertField').value+'}',editor.selectionStart,editor.selectionEnd,'end');editor.focus();render()};
$('scale').oninput=render;
for(const id of ['timeMode',...Object.keys(conventionControls)])$(id).onchange=()=>{data=null;$('grid').replaceChildren();$('sankalpa').textContent='Loading selected calendar view…';syncAudioText();load()};
$('reset').onclick=()=>{$('template').value=selected.country==='United States'?familyTemplates[$('lang').value]:fullTemplates[$('lang').value];render()};
$('save').onclick=()=>{for(const key of ['gotra','lang','timeMode','scale','form',...Object.keys(conventionControls)])save(key,$(key).value);$('settings').classList.add('hide');render();load()};
function setDisplay(on){document.body.classList.toggle('display-mode',on);$('calendarSummary').classList.toggle('hide',!on);$('display').textContent=on?'Exit home display':'Home display';save('display',on?'1':'0')}
setDisplay(params.has('display')?params.get('display')==='1':read('display')==='1');
$('display').onclick=()=>setDisplay(!document.body.classList.contains('display-mode'));
$('fullscreen').onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await document.documentElement.requestFullscreen()}catch{$('status').textContent='Full screen is unavailable in this browser. Home display mode still works.'}};
let audioText='', audioScript='', audioVersion=0, audioRequest=null, audioBusy=false;
const hostedAudioCache=new Map();
function syncAudioText(){
 const script=$('lang').value, text=data?.calendar_audio?.[script]||'';
 $('audioPreview').textContent=text||'Calendar audio is unavailable until valid calendar values are loaded.';
 $('audioPreview').lang={roman:'sa-Latn',sanskrit:'sa',kannada:'sa-Knda'}[script];
 if(text!==audioText||script!==audioScript){
  audioText=text;audioScript=script;audioVersion++;audioRequest?.abort();audioBusy=false;
  $('audioPlayer').pause();$('audioPlayer').removeAttribute('src');$('audioPlayer').load();$('audioPlayer').hidden=true;
  $('downloadAudio').classList.add('hide');$('downloadAudio').removeAttribute('href');
  $('audioStatus').textContent='Generate the changing calendar fields, then press Play. Audio is Sanskrit in all three display scripts.';
 }
 $('generateAudio').disabled=!data||!text||audioBusy||(data.review_required);
}
async function audioJSON(url,options={}){
 const response=await fetch(url,{...options,signal:audioRequest.signal});
 const result=await response.json();
 if(!response.ok)throw Error(typeof result.detail==='string'?result.detail:'Audio request failed (HTTP '+response.status+')');
 return result;
}
$('generateAudio').onclick=async()=>{
 if(!data||audioBusy||(data.review_required))return;
 const version=audioVersion, cacheKey=data.calendar_audio.sanskrit;
 audioBusy=true;audioRequest=new AbortController();$('generateAudio').disabled=true;
 $('audioStatus').textContent='Checking the local cache / requesting Vagdhenu… First generation may take several minutes.';
 const timeout=setTimeout(()=>audioRequest?.abort(),330000);
 try{
  let job=hostedAudioCache.has(cacheKey)?{...hostedAudioCache.get(cacheKey),cached:true}:await audioJSON('/api/audio',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:audioText,script:audioScript})});
  while(version===audioVersion&&['queued','generating'].includes(job.state)){
   $('audioStatus').textContent=job.state==='queued'?'Queued for Vagdhenu generation…':'Generating with Vagdhenu… You can keep using the display.';
   await new Promise(resolve=>setTimeout(resolve,1500));
   if(version!==audioVersion)return;
   job=await audioJSON('/api/audio/'+job.id);
  }
  if(version!==audioVersion)return;
  if(job.state!=='ready')throw Error(job.error||'Audio generation failed.');
  if(job.url.startsWith('data:audio/wav;base64,')){
   if(hostedAudioCache.size>=8)hostedAudioCache.delete(hostedAudioCache.keys().next().value);
   hostedAudioCache.set(cacheKey,job);
  }
  $('audioPlayer').src=job.url;$('audioPlayer').hidden=false;$('audioPlayer').load();
  $('audioPlayer').playbackRate=Number($('audioSpeed').value);$('audioPlayer').loop=$('repeatAudio').checked;
  $('downloadAudio').href=job.url;$('downloadAudio').classList.remove('hide');
  $('audioStatus').textContent='Audio ready'+(job.cached?' from cache':'')+'. Press Play below. Review the pronunciation before using it as a guide.';
 }catch(error){if(version===audioVersion)$('audioStatus').textContent=error.name==='AbortError'?'The audio request timed out. Try again to check the cache.':'Audio unavailable: '+error.message;}
 finally{clearTimeout(timeout);if(version===audioVersion){audioBusy=false;syncAudioText()}}
};
$('audioSpeed').onchange=()=>{$('audioPlayer').playbackRate=Number($('audioSpeed').value)};
$('repeatAudio').onchange=()=>{$('audioPlayer').loop=$('repeatAudio').checked};
$('audioPlayer').onerror=()=>{$('audioStatus').textContent='Audio could not be loaded. Check the server and try Generate audio again.'};

syncMode();clock();initialise();setInterval(clock,30000);setInterval(load,60000);
document.addEventListener('visibilitychange',()=>{if(!document.hidden){clock();load()}});
