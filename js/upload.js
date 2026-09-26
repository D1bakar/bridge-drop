/* M0 upload — drop file → POST /v1/files with progress label.
 * Design: label swaps to heading-sm on dragover (CSS); text updates only.
 * Backend down → "Backend off — is :8000 running?" Mock list untouched (c4 refreshes it).
 * Single-terminal mode (:8000) uses same origin; Live Server mode uses :8000 on same host.
 */

const API_BASE = (() => {
  try {
    if (window.location.port === "8000" && window.location.origin.startsWith("http")) {
      return window.location.origin.replace(/\/$/, "");
    }
  } catch (_) {}
  const raw = window.location.hostname || "localhost";
  // localhost can resolve to ::1 while uvicorn binds 127.0.0.1 — prefer IPv4.
  const host = raw === "localhost" ? "127.0.0.1" : raw;
  return `http://${host}:8000`;
})();

function setDropLabel(text) {
  const label = document.querySelector("#dropzone .dropzone-label");
  if (label) label.textContent = text;
}

function setTx(frac) {
  // Drives the pulse journey across the bridge mark (R3 transfer motion).
  const zone = document.getElementById("dropzone");
  if (zone) zone.style.setProperty("--tx", Math.max(0, Math.min(1, frac || 0)));
}

function flashDone() {
  const zone = document.getElementById("dropzone");
  if (!zone) return;
  setTx(1);
  zone.classList.add("is-done");
  setTimeout(() => {
    zone.classList.remove("is-done");
    setTx(0);
  }, 1400);
}

function setLoading(on) {
  // Bridge mark breathes while bytes move; null-safe off Home.
  const mark = document.querySelector(".bridge-mark") || document.querySelector(".glyph");
  if (mark) mark.classList.toggle("is-loading", !!on);
  try {
    document.body.classList.toggle("is-transferring", !!on);
  } catch (_) {}
}

function uploadFile(file) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE}/v1/files`);
    xhr.upload.addEventListener("progress", (e) => {
      if (e.lengthComputable) {
        setDropLabel(`Uploading ${Math.round((e.loaded / e.total) * 100)}%`);
        setTx(e.total ? e.loaded / e.total : 0);
      } else {
        setDropLabel("Uploading…");
      }
    });
    xhr.addEventListener("load", () => {
      setLoading(false);
      if (xhr.status === 201) {
        setDropLabel("Received →");
        flashDone();
        resolve(JSON.parse(xhr.responseText));
      } else {
        setDropLabel("Failed — try again");
        setTx(0);
        reject(new Error(`upload ${xhr.status}`));
      }
    });
    xhr.addEventListener("error", () => {
      setLoading(false);
      setDropLabel("Backend off — is :8000 running?");
      setTx(0);
      reject(new Error("network"));
    });
    const form = new FormData();
    form.append("file", file, file.name);
    setDropLabel("Uploading 0%");
    setLoading(true);
    xhr.send(form);
  });
}

function initUpload() {
  const zone = document.getElementById("dropzone");
  if (!zone) return;
  const sendFirst = (files) => {
    if (!files || files.length === 0) return;
    uploadFile(files[0])
      .then(() => {
        if (window.BridgeRecent) window.BridgeRecent.refresh();
      })
      .catch(() => {});
  };
  zone.addEventListener("drop", (e) => {
    sendFirst(e.dataTransfer && e.dataTransfer.files);
  });
  // Phone path: no drag-drop on touch — native picker via the label.
  const picker = document.getElementById("file-input");
  if (picker) {
    picker.addEventListener("change", () => {
      sendFirst(picker.files);
      picker.value = ""; // allow re-picking the same file
    });
  }
}

document.addEventListener("DOMContentLoaded", initUpload);

window.BridgeUpload = { API_BASE, uploadFile };
window.BridgeSpin = setLoading;
