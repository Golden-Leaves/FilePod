console.log("[FilePod] main.js LOADED");
//Helpers
function fmtBytes(bytes) {
  if (!bytes) return "—";
  const units = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return (bytes / Math.pow(1024, i)).toFixed(1) + " " + units[i];
}

function timeLeft(expiry) {
  const ms = expiry - Date.now();
  if (ms <= 0) return "Expired";
  const mins = Math.floor(ms / 60000);
  const secs = Math.floor((ms % 60000) / 1000);
  return `${mins}m ${secs}s`;
}

function renderTable() {
  const tbody = document.getElementById("rows");
  tbody.innerHTML = items.map(it => `
    <tr>
      <td><input type="checkbox"></td>
      <td>${it.name}</td>
      <td>${it.kind === "folder" ? "Folder" : (it.mime?.split("/")[1] || "File")}</td>
      <td class="text-end">${it.kind==="folder" ? "—" : fmtBytes(it.size)}</td>
      <td>${timeLeft(it.expiresAt)}</td>
      <td class="text-end">${it.downloads}</td>
      <td>${it.status}</td>
      <td>
        <button class="btn btn-sm btn-outline-primary">Download</button>
        <button class="btn btn-sm btn-outline-secondary">Copy Link</button>
        <button class="btn btn-sm btn-outline-danger">Delete</button>
      </td>
    </tr>
  `).join("");
}
// --- CONFIG ---
let ttlMinutes = 60; // or read from your TTL input if you have one

// --- UPLOAD CORE ---
// Sends files (and optional folder structure) to Flask /upload
async function uploadFilesToServer(files, { preservePaths = true } = {}) {
  const fd = new FormData();
  for (const f of files) {
    // Preserve folder structure if available (from <input webkitdirectory>)
    const name = (preservePaths && f.webkitRelativePath) ? f.webkitRelativePath : f.name;
    // 1) 'files' is what Flask will read via request.files.getlist("files")
    // 2) Third arg sets filename seen by Flask; can include subpaths
    fd.append("files", f, name);
  }
  fd.append("ttl_minutes", String(ttlMinutes)); // so backend can compute expires_at

  // NOTE: Do NOT set Content-Type manually; the browser sets correct multipart boundary
  const res = await fetch("/upload", { method: "POST", body: fd }); //hit the upload route
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Upload failed (${res.status}): ${text}`);
  }
  return res.json(); // expect { uploaded: [{token, orig_name, size, expires_at, downloads}], errors: [] }
}

// --- REFRESH CORE ---
// Pull live inventory from server to render (keeps your table in sync with DB)
async function fetchFilesFromServer() {
  const res = await fetch("/files"); // GET route that returns current non-expired items
  if (!res.ok) throw new Error("Failed to fetch file list");
  return res.json(); // expect [{token, orig_name, size, expires_at, downloads, kind?}]
}

async function refreshFromServer() {
  const data = await fetchFilesFromServer();
  // Optional: sync your local mock 'items' from server for renderTable()
  items.length = 0;
  for (const r of data) {
    items.push({
      id: r.token,                               // use token as id
      name: r.orig_name || r.name,
      kind: r.kind || "file",
      mime: r.mime || "",
      size: r.size || 0,
      expiresAt: Date.parse(r.expires_at) || (Date.now() + 60*60*1000),
      downloads: r.downloads ?? r.hit_count ?? 0,
      status: "active",
      password: !!r.password
    });
  }
  renderTable();
}

// --- DROPZONE DIRECTORY SUPPORT (optional advanced) ---
// If you want to support directory drag-drop (not just files) via DataTransferItem API.
async function gatherDroppedFiles(dataTransfer) {
  if (!dataTransfer.items) return [...(dataTransfer.files || [])];

  const entries = [];
  for (const item of dataTransfer.items) {
    const entry = item.webkitGetAsEntry?.();
    if (entry) entries.push(entry);
  }
  const files = [];
  async function walk(entry, pathPrefix = "") {
    if (entry.isFile) {
      await new Promise(resolve => {
        entry.file(file => {
          // Inject a synthetic relative path so we can preserve structure
          Object.defineProperty(file, "webkitRelativePath", {
            value: pathPrefix + file.name,
            configurable: true
          });
          files.push(file);
          resolve();
        });
      });
    } else if (entry.isDirectory) {
      const reader = entry.createReader();
      const readAll = () => new Promise(resolve => {
        reader.readEntries(async (ents) => {
          if (!ents.length) return resolve();
          for (const e of ents) await walk(e, pathPrefix + entry.name + "/");
          resolve(await readAll());
        });
      });
      await readAll();
    }
  }
  for (const e of entries) await walk(e, "");
  return files;
}


// File picker (single/multi)
document.getElementById("file-input").addEventListener("change", async (e) => {
  const files = [...e.target.files];
  if (!files.length) return;
  try {
    await uploadFilesToServer(files, { preservePaths: false }); // picker has no relative paths
    await refreshFromServer();
  } catch (err) {
    console.error(err);
    alert(String(err.message || err));
  } finally {
    e.target.value = "";
  }
});

// Drag & drop (files OR folders)
const dropzone = document.getElementById("dropzone");
dropzone.addEventListener("dragover", e => { e.preventDefault(); dropzone.classList.add("is-over"); });
["dragleave","drop"].forEach(evt => dropzone.addEventListener(evt, e => dropzone.classList.remove("is-over")));
dropzone.addEventListener("drop", async (e) => {
  e.preventDefault();
  try {
    const files = await gatherDroppedFiles(e.dataTransfer);
    if (!files.length) return;
    await uploadFilesToServer(files, { preservePaths: true });
    await refreshFromServer();
  } catch (err) {
    console.error(err);
    alert(String(err.message || err));
  }
});

// Initial paint (pull what the server already has)
refreshFromServer().catch(console.error);


document.addEventListener("DOMContentLoaded", () => {
  const fileInput   = document.getElementById("file-input");
  const folderInput = document.getElementById("folder-input");
  const dropzone    = document.getElementById("dropzone");

  console.log("[FilePod] main.js loaded");

  // 1) File picker (multi)
  fileInput.addEventListener("change", async (e) => {
    const files = [...e.target.files];
    console.log("[FilePod] file-input change:", files.length);
    if (!files.length) return;
    await uploadFilesToServer(files, { preservePaths: false });
    await refreshFromServer();
    e.target.value = ""; // allow re-pick same files
  });

  // 2) Folder picker (webkitdirectory)
  folderInput.addEventListener("change", async (e) => {
    const files = [...e.target.files];
    console.log("[FilePod] folder-input change:", files.length);
    if (!files.length) return;
    await uploadFilesToServer(files, { preservePaths: true }); // uses webkitRelativePath
    await refreshFromServer();
    e.target.value = "";
  });

  // 3) Drag anywhere – prevent browser from opening files
  ["dragenter","dragover","dragleave","drop"].forEach(evt => {
    document.addEventListener(evt, ev => {
      ev.preventDefault(); ev.stopPropagation();
    });
  });

  // Visual highlight over dropzone only
  ["dragenter","dragover"].forEach(evt =>
    dropzone.addEventListener(evt, e => dropzone.classList.add("is-over"))
  );
  ["dragleave","drop"].forEach(evt =>
    dropzone.addEventListener(evt, e => dropzone.classList.remove("is-over"))
  );

  dropzone.addEventListener("drop", async (e) => {
    const dt = e.dataTransfer;
    const files = dt?.items ? await gatherDroppedFiles(dt) : [...(dt?.files || [])];
    console.log("[FilePod] drop:", files.length);
    if (!files.length) return;
    await uploadFilesToServer(files, { preservePaths: true });
    await refreshFromServer();
  });

  // --- Core upload/fetch ---
  async function uploadFilesToServer(files, { preservePaths = true } = {}) {
    const fd = new FormData();
    for (const f of files) {
      const name = (preservePaths && f.webkitRelativePath) ? f.webkitRelativePath : f.name;
      fd.append("files", f, name);
    }
    fd.append("ttl_minutes", "60");
    const res = await fetch("/upload", { method: "POST", body: fd });
    if (!res.ok) {
      const t = await res.text().catch(()=> "");
      throw new Error(`Upload failed ${res.status}: ${t}`);
    }
    return res.json();
  }

  async function refreshFromServer() {
    const res = await fetch("/files");
    const rows = await res.json();
    const items = rows.map(r => ({
      id: r.token,
      name: r.orig_name,
      kind: "file",
      mime: r.mime || "",
      size: r.size || 0,
      expiresAt: Date.parse(r.expires_at) || (Date.now()+60*60*1000),
      downloads: r.hit_count || 0,
      status: "active"
    }));
    render(items);
  }

  function render(items) {
    const tbody = document.getElementById("rows");
    tbody.innerHTML = items.map(it => `
      <tr>
        <td><input type="checkbox"></td>
        <td>${it.name}</td>
        <td>${it.mime.split("/")[1] || "File"}</td>
        <td class="text-end">${fmtBytes(it.size)}</td>
        <td>${timeLeft(it.expiresAt)}</td>
        <td class="text-end">${it.downloads}</td>
        <td>${it.status}</td>
        <td><a class="btn btn-sm btn-outline-primary" href="/d/${it.id}">Download</a></td>
      </tr>
    `).join("");
  }

  // Optional: directory drag (keeps subfolders)
  async function gatherDroppedFiles(dataTransfer) {
    const entries = [];
    for (const item of dataTransfer.items) {
      const e = item.webkitGetAsEntry?.();
      if (e) entries.push(e);
    }
    const files = [];
    async function walk(entry, prefix="") {
      if (entry.isFile) {
        await new Promise(resolve => entry.file(file => {
          Object.defineProperty(file, "webkitRelativePath", { value: prefix + file.name, configurable: true });
          files.push(file); resolve();
        }));
      } else if (entry.isDirectory) {
        const reader = entry.createReader();
        await new Promise(resolve => reader.readEntries(async ents => {
          for (const e of ents) await walk(e, prefix + entry.name + "/");
          resolve();
        }));
      }
    }
    for (const e of entries) await walk(e, "");
    return files;
  }

  // First paint
  refreshFromServer().catch(console.error);
});
