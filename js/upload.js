/* M0 upload — drop file → POST /v1/files with progress label.
 * Design: label swaps to heading-sm on dragover (CSS); text updates only.
 * Backend down → "Backend off — is :8000 running?" Mock list untouched (c4 refreshes it).
 */

const API_BASE = `http://${window.location.hostname || "localhost"}:8000`;

function setDropLabel(text) {
  const label = document.querySelector("#dropzone .dropzone-label");
  if (label) label.textContent = text;
}

function uploadFile(file) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE}/v1/files`);
    xhr.upload.addEventListener("progress", (e) => {
      if (e.lengthComputable) {
        setDropLabel(`Uploading ${Math.round((e.loaded / e.total) * 100)}%`);
      } else {
        setDropLabel("Uploading…");
      }
    });
    xhr.addEventListener("load", () => {
      if (xhr.status === 201) {
        setDropLabel("Received →");
        resolve(JSON.parse(xhr.responseText));
      } else {
        setDropLabel("Failed — try again");
        reject(new Error(`upload ${xhr.status}`));
      }
    });
    xhr.addEventListener("error", () => {
      setDropLabel("Backend off — is :8000 running?");
      reject(new Error("network"));
    });
    const form = new FormData();
    form.append("file", file, file.name);
    setDropLabel("Uploading 0%");
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
