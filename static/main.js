console.log("[FilePod] main.js loaded");

// ---- helpers you already had ----
function fmtBytes(bytes){ if(!bytes) return "—"; const u=["B","KB","MB","GB"]; const i=Math.floor(Math.log(bytes)/Math.log(1024)); return (bytes/Math.pow(1024,i)).toFixed(1)+" "+u[i]; }
function timeLeft(expiry){ const ms=expiry-Date.now(); if(ms<=0) return "Expired"; const m=Math.floor(ms/60000), s=Math.floor((ms%60000)/1000); return `${m}m ${s}s`; }

let ttlMinutes = 60;

async function uploadFilesToServer(files,{preservePaths=true}={}){
  console.log("[FilePod] preparing POST /upload with", files.length, "file(s)");
  const fd = new FormData();
  for (const f of files) {
    const name = (preservePaths && f.webkitRelativePath) ? f.webkitRelativePath : f.name;
    fd.append("files", f, name);
  }
  fd.append("ttl_minutes", String(ttlMinutes));
  const res = await fetch("/upload", { method: "POST", body: fd });
  console.log("[FilePod] POST /upload ->", res.status);
  if (!res.ok) throw new Error(await res.text().catch(()=> "upload failed"));
  return res.json();
}

async function fetchFilesFromServer(){
  const res = await fetch("/files");
  console.log("[FilePod] GET /files ->", res.status);
  if (!res.ok) throw new Error("Missing /files route");
  return res.json();
}

function renderTableFromRows(rows){
  const items = rows.map(r => ({
    id: r.token,
    name: r.name,
    kind: "file",
    // prefer server-provided type; otherwise derive from mime; fallback to "File"
    type: r.type || (r.mime ? (r.mime.split("/")[0] || "File") : "File"),
    mime: r.mime || null,
    size: r.size || 0,
    expiresAt: Date.parse(r.expires_at) || (Date.now() + 60*60*1000),
    downloads: r.download_count || r.downloads || 0,
    status: "active"
  }));

  const tbody = document.getElementById("rows");
  tbody.innerHTML = items.map(it => `
    <tr>
      <td><input type="checkbox"></td>
      <td>${it.name}</td>
      <td>${it.type}</td>
      <td class="text-end">${fmtBytes(it.size)}</td>
      <td>${timeLeft(it.expiresAt)}</td>
      <td class="text-end">${it.downloads}</td>
      <td>${it.status}</td>
      <td><a class="btn btn-sm btn-outline-primary" href="/d/${it.id}">Download</a></td>
    </tr>
  `).join("");
}

async function refresh(){ renderTableFromRows(await fetchFilesFromServer()); }

// ---- SINGLE wiring only (no second copy anywhere else) ----
document.addEventListener("DOMContentLoaded", () => {
  const fileInput   = document.getElementById("file-input");
  const folderInput = document.getElementById("folder-input");
  const dropzone    = document.getElementById("dropzone");

  // prevent browser navigating on drop anywhere
  ["dragenter","dragover","dragleave","drop"].forEach(evt=>{
    document.addEventListener(evt, e=>{ e.preventDefault(); e.stopPropagation(); }, {passive:false});
  });

  fileInput?.addEventListener("change", async e=>{
    const files=[...e.target.files];
    console.log("[FilePod] file-input change:", files.length);
    if (!files.length) return;
    await uploadFilesToServer(files, {preservePaths:false});
    await refresh();
    e.target.value="";
  });

  folderInput?.addEventListener("change", async e=>{
    const files=[...e.target.files];
    console.log("[FilePod] folder-input change:", files.length);
    if (!files.length) return;
    await uploadFilesToServer(files, {preservePaths:true});
    await refresh();
    e.target.value="";
  });

  dropzone?.addEventListener("drop", async e=>{
    const files = [...(e.dataTransfer?.files || [])];
    console.log("[FilePod] drop:", files.length);
    if (!files.length) return;
    await uploadFilesToServer(files, {preservePaths:true});
    await refresh();
  });

  refresh().catch(console.error);
});
