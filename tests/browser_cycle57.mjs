/**
 * Cycle 57 — actual headless Chromium regression of public offline HTML.
 *
 * This script executes browser actions, NOT a human accessibility audit.
 * Tests only synthetic public content: no personal, OEM or mining data.
 * It refuses external requests and records a bounded local screenshot set.
 */
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import os from "node:os";
import {pathToFileURL} from "node:url";
import {chromium} from "playwright";

const ROOT=path.resolve(path.dirname(new URL(import.meta.url).pathname),"..");
const REPORT_DIR=path.join(ROOT,"build","browser-cycle57");
const BASE_PATHS={
  workbench:"review/qa_portais_56.html",
  knowledge:"portal/index.html",
  audit:"portal/auditoria.html",
  versions:"portal/versoes.html",
};
const outcomes=[],screenshots=[];
let browser;
await fs.mkdir(REPORT_DIR,{recursive:true});

function record(name,success,detail=""){
 outcomes.push({name,passed:success,detail:String(detail).slice(0,450)});
}
async function scenario(name,action){
 try{await action();record(name,true);console.log("PASS",name)}
 catch(error){record(name,false,error?.stack??String(error));console.error("FAIL",name,error)}
}
function urlFor(which){
 return pathToFileURL(path.join(ROOT,BASE_PATHS[which])).href;
}
async function contextPage(which,options={}){
 const context=await browser.newContext({viewport:options.viewport??{width:1280,height:800},
   acceptDownloads:true,locale:"pt-BR",colorScheme:"dark",reducedMotion:"reduce"});
 const page=await context.newPage();
 const pageErrors=[],remoteRequests=[];
 page.on("pageerror",e=>pageErrors.push(e.message));
 page.on("request",req=>{
   if(/^https?:/i.test(req.url()))remoteRequests.push(req.url());
 });
 await page.route(/^https?:\/\//,route=>route.abort("blockedbyclient"));
 const result=await page.goto(urlFor(which),{waitUntil:"load",timeout:15000});
 assert.equal(result?.status(),200,"local file load status");
 return {page,context,pageErrors,remoteRequests,
  async close(){
   assert.deepEqual(pageErrors,[],"browser JavaScript threw an exception");
   assert.deepEqual(remoteRequests,[],"offline file attempted external network request");
   await context.close();
  }
 };
}
async function downloadJson(page,selector){
 const pending=page.waitForEvent("download");
 await page.locator(selector).click();
 const download=await pending,filepath=await download.path();
 assert.ok(filepath,"download produced no file");
 const json=JSON.parse(await fs.readFile(filepath,"utf8"));
 return json;
}
async function checkViewport(which,width){
 const view=await contextPage(which,{viewport:{width,height:820}});
 try{
  const {page}=view;
  const stats=await page.evaluate(()=>({
   screen:innerWidth,
   document:document.documentElement.scrollWidth,
   body:document.body.scrollWidth,
   headings:[...document.querySelectorAll("h1")].map(x=>x.textContent.trim()),
  }));
  assert.ok(stats.headings.length>=1,which+": no h1");
  assert.ok(stats.document<=width+2,
    which+" "+width+"px: unexpected document overflow "+JSON.stringify(stats));
  assert.equal(await page.getByText("NO GO OPERACIONAL",{exact:false}).count()>0,true);
  if(width===375){
   const name=which+"-375.png";
   await page.screenshot({path:path.join(REPORT_DIR,name),fullPage:false});
   screenshots.push(name);
  }
 }finally{await view.close()}
}
async function run(){
 browser=await chromium.launch({headless:true});
 await scenario("qa_initial_eight_unexecuted",async()=>{
  const v=await contextPage("workbench");
  try{
   assert.equal(await v.page.locator(".test").count(),8);
   assert.match(await v.page.locator("#metrics").innerText(),/8/);
   assert.equal(await v.page.locator("#status-mobile_layout").inputValue(),"not_tested");
   assert.match(await v.page.locator("body").innerText(),/NO GO OPERACIONAL/);
  }finally{await v.close()}
 });
 await scenario("qa_export_import_resume_failed_and_passed",async()=>{
  const v=await contextPage("workbench");
  try{
   const p=v.page;
   await p.locator("#platform").fill("Chromium Linux · testes sintéticos");
   await p.locator("#release").fill("b930a177cc9ba1c94c32785f8fa0b16c37723afb");
   await p.locator("#status-mobile_layout").selectOption("failed");
   await p.locator("#notes-mobile_layout").fill("Achado sintético para testar relatório parcial");
   await p.locator("#evidence-mobile_layout").fill("synthetic-issue-C57-01");
   await p.locator("#status-keyboard_skip_focus").selectOption("passed");
   await p.locator("#notes-keyboard_skip_focus").fill("Ensaio fictício de serialização; não é revisão humana");
   await p.locator("#evidence-keyboard_skip_focus").fill("synthetic-issue-C57-02");
   const json=await downloadJson(p,"#export");
   assert.equal(json.checks.length,8);
   assert.equal(json.checks[0].status,"failed");
   assert.equal(json.checks[2].status,"passed");
   assert.equal(json.humanReviewCompleted,false);
   assert.equal(json.operationalAuthorityGranted,false);
   assert.equal(json.mechanicalDiagnosticAccuracyValidated,false);
   assert.equal(json.decision,"NO GO");
   await p.reload();
   assert.equal(await p.locator("#status-mobile_layout").inputValue(),"not_tested");
   await p.locator("#file").setInputFiles({name:"partial.json",mimeType:"application/json",
    buffer:Buffer.from(JSON.stringify(json),"utf8")});
   await p.getByText("Relatório importado e restaurado",{exact:false}).waitFor();
   assert.equal(await p.locator("#status-mobile_layout").inputValue(),"failed");
   assert.equal(await p.locator("#notes-mobile_layout").inputValue(),
    "Achado sintético para testar relatório parcial");
   assert.equal(await p.locator("#status-keyboard_skip_focus").inputValue(),"passed");
   assert.match(await p.locator("#metrics").innerText(),/Falhas \/ bloqueios/);
   const again=await downloadJson(p,"#export");
   assert.deepEqual(again,json,"import/export round trip is not lossless");
  }finally{await v.close()}
 });
 await scenario("qa_forged_signoff_import_rejected",async()=>{
  const v=await contextPage("workbench");
  try{
   const p=v.page;
   await p.locator("#notes-mobile_layout").fill("Sessão sintética em andamento");
   const original=await downloadJson(p,"#export");
   const forged=structuredClone(original);
   forged.humanReviewCompleted=true;
   forged.operationalAuthorityGranted=true;
   forged.decision="GO";
   await p.locator("#file").setInputFiles({name:"forged.json",mimeType:"application/json",
    buffer:Buffer.from(JSON.stringify(forged),"utf8")});
   await p.getByText("Importação recusada",{exact:false}).waitFor();
   const after=await downloadJson(p,"#export");
   assert.deepEqual(after,original,"invalid import changed existing session");
   const xss=structuredClone(original);
   xss.observedPlatform="<img src=x onerror=alert(1)>";
   await p.locator("#file").setInputFiles({name:"xss.json",mimeType:"application/json",
    buffer:Buffer.from(JSON.stringify(xss),"utf8")});
   await p.getByText("Relatório importado e restaurado",{exact:false}).waitFor();
   assert.equal(await p.locator("#platform").inputValue(),xss.observedPlatform);
   assert.equal(await p.locator("#platform img").count(),0);
  }finally{await v.close()}
 });
 await scenario("qa_eight_self_reported_passed_never_signoff",async()=>{
  const v=await contextPage("workbench");
  try{
   const p=v.page;
   for(const id of ["mobile_layout","zoom_reflow","keyboard_skip_focus","audit_tabs",
     "screen_reader","status_clarity","export_integrity","sources_permissions"]){
     await p.locator("#status-"+id).selectOption("passed");
     await p.locator("#notes-"+id).fill("Resultado sintético do teste de serialização: NÃO testado por humano");
     await p.locator("#evidence-"+id).fill("synthetic-browser-"+id);
   }
   const result=await downloadJson(p,"#export");
   assert.ok(result.checks.every(c=>c.status==="passed"));
   assert.equal(result.humanReviewCompleted,false);
   assert.equal(result.operationalAuthorityGranted,false);
   assert.equal(result.decision,"NO GO");
   assert.match(await p.locator("#interpretation").innerText(),/não há aprovação profissional/i);
  }finally{await v.close()}
 });
 await scenario("audit_keyboard_tabs_and_gate_filter",async()=>{
  const v=await contextPage("audit");
  try{
   const p=v.page;
   await p.locator("#tab-gates").focus();
   await p.keyboard.press("ArrowRight");
   assert.equal(await p.locator("#tab-prs").getAttribute("aria-selected"),"true");
   assert.equal(await p.locator("#prs").isVisible(),true);
   assert.equal(await p.locator("#gates").isVisible(),false);
   await p.keyboard.press("End");
   assert.equal(await p.locator("#tab-limites").getAttribute("aria-selected"),"true");
   assert.equal(await p.locator("#limites").isVisible(),true);
   await p.keyboard.press("Home");
   assert.equal(await p.locator("#tab-gates").getAttribute("aria-selected"),"true");
   assert.equal(await p.locator("#gates").isVisible(),true);
   await p.locator("#query").fill("____nao_existe____");
   await p.locator("#noresults").waitFor({state:"visible"});
   assert.match(await p.locator("body").innerText(),/NO GO/);
   const exported=await downloadJson(p,"#export");
   assert.equal(exported.gates.length,13);
   assert.equal(exported.project.decision,"NO GO");
  }finally{await v.close()}
 });
 await scenario("knowledge_filter_theme_export",async()=>{
  const v=await contextPage("knowledge");
  try{
   const p=v.page;
   assert.match(await p.locator("#count").innerText(),/resultados/);
   await p.locator("#search").fill("____nao_existe____");
   await p.locator("#empty").waitFor({state:"visible"});
   assert.match(await p.locator("#count").innerText(),/^0 resultados/);
   await p.locator("#search").fill("");
   await p.locator("#theme").click();
   assert.equal(await p.locator("body").evaluate(x=>x.classList.contains("light")),true);
   const exported=await downloadJson(p,"#download");
   assert.equal(exported.project.decision,"NO GO");
   assert.equal(exported.gates.length,13);
   assert.equal(exported.sites.length,3);
  }finally{await v.close()}
 });
 await scenario("versions_comparison_and_diff_export",async()=>{
  const v=await contextPage("versions");
  try{
   const p=v.page;
   assert.equal(await p.locator("#publication article").count(),2);
   await p.locator("#from").selectOption("published");
   await p.locator("#to").selectOption("published");
   assert.match(await p.locator("#counts").innerText(),/Exibindo: 0 de 0/);
   await p.locator("#from").selectOption("baseline");
   await p.locator("#to").selectOption("current");
   const n=await p.locator("#changes tr").count();
   assert.ok(n>=3,"expected historical changes");
   const report=await downloadJson(p,"#download");
   assert.equal(report.sourceSnapshot,"baseline");
   assert.equal(report.targetSnapshot,"current");
   assert.ok(report.changes.length>=3);
   assert.equal(report.operationallyApproved,false);
   assert.equal(report.externallyApproved,false);
  }finally{await v.close()}
 });
 await scenario("all_four_responsive_320_375_390_768",async()=>{
  for(const name of Object.keys(BASE_PATHS))for(const width of [320,375,390,768]){
   await checkViewport(name,width);
  }
 });
 await scenario("keyboard_skip_links_reach_main",async()=>{
  for(const which of Object.keys(BASE_PATHS)){
   const v=await contextPage(which);
   try{
    const p=v.page;
    await p.keyboard.press("Tab");
    const name=await p.evaluate(()=>document.activeElement?.className);
    assert.match(name,/skip/,"no initial keyboard skip link on "+which);
    await p.keyboard.press("Enter");
    const hash=await p.evaluate(()=>location.hash);
    assert.equal(hash,which==="workbench"?"#content":"#main-content");
   }finally{await v.close()}
  }
 });
}
try{await run()}catch(error){record("harness_fatal",false,error?.stack??String(error))}
finally{
 await browser?.close();
 const failures=outcomes.filter(o=>!o.passed);
 const summary={
  schema:"maintenance-superinteligence.cycle57-real-browser-automation.v1",
  browser:"Chromium headless via Playwright",
  testFramework:"Node.js + Playwright 1.56.1",
  testedLocalOfflineHtmlFiles:Object.values(BASE_PATHS),
  executedBrowserScenarios:outcomes.length,
  passedBrowserScenarios:outcomes.filter(o=>o.passed).length,
  failedBrowserScenarios:failures.length,
  responsiveWidthsCssPx:[320,375,390,768],
  screenshots,
  results:outcomes,
  actualHumanQAExecutions:0,
  screenReaderAudited:false,
  WCAGConformanceCertified:false,
  mechanicalReliabilityValidated:false,
  externalStudyGatesVerified:0,
  SAPWriteAuthorized:false,
  operationalAuthorityGranted:false,
  decision:"NO GO"
 };
 await fs.writeFile(path.join(REPORT_DIR,"summary.json"),JSON.stringify(summary,null,2)+"\n");
 console.log("BROWSER QA SUMMARY",JSON.stringify({
  passed:summary.passedBrowserScenarios,
  failed:summary.failedBrowserScenarios,
  screenshots:screenshots.length,
  human:0,
  decision:"NO GO"}));
 if(failures.length)process.exitCode=1;
}
