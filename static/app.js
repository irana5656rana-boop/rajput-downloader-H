const urlInput = document.getElementById("url");
const pasteBtn = document.getElementById("pasteBtn");
const downloadBtn = document.getElementById("downloadBtn");
const statusBox = document.getElementById("status");
const resultContent = document.getElementById("resultContent");

let mode = "video";
let quality = "720";
let platform = "TikTok";

// PLATFORM SWITCH
document.querySelectorAll(".platform").forEach(btn => {
  btn.addEventListener("click", () => {

    document.querySelectorAll(".platform").forEach(x => {
      x.classList.remove("active");
    });

    btn.classList.add("active");
    platform = btn.textContent.trim();

    const placeholders = {
      "TikTok": "Paste TikTok video URL here",
      "Instagram": "Paste Instagram video URL here",
      "Facebook": "Paste Facebook video URL here",
      "YouTube": "Paste YouTube video URL here",
      "Audio / Song": "Paste video or song URL here"
    };

    urlInput.placeholder =
      placeholders[platform] || "Paste video URL here";

    statusBox.textContent = platform + " selected ✅";
  });
});

// PASTE
pasteBtn.addEventListener("click", async () => {
  try {
    const text = await navigator.clipboard.readText();
    urlInput.value = text;
    statusBox.textContent = "URL pasted successfully.";
  } catch {
    statusBox.textContent = "Clipboard permission nahi mili.";
  }
});

// VIDEO / AUDIO
document.querySelectorAll(".mode").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".mode").forEach(x =>
      x.classList.remove("active")
    );

    btn.classList.add("active");
    mode = btn.dataset.mode;
  });
});

// QUALITY
document.querySelectorAll(".quality").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".quality").forEach(x =>
      x.classList.remove("active")
    );

    btn.classList.add("active");
    quality = btn.dataset.quality;
  });
});

// GET VIDEO INFO
async function getInfo(url) {
  const response = await fetch("/api/info", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ url })
  });

  return await response.json();
}

// DOWNLOAD
downloadBtn.addEventListener("click", async () => {

  const url = urlInput.value.trim();

  if (!url) {
    statusBox.textContent = "Pehle video URL paste karo.";
    return;
  }

  downloadBtn.disabled = true;
  downloadBtn.textContent = "PROCESSING...";

  statusBox.textContent =
    platform + " video information check ho rahi hai...";

  try {

    const info = await getInfo(url);

    if (!info.success) {
      throw new Error(
        info.error || "Video information nahi mili."
      );
    }

    resultContent.innerHTML = `
      <strong>${escapeHtml(info.title || "Video")}</strong>
      ${info.uploader ? `<br>By: ${escapeHtml(info.uploader)}` : ""}
      <br><br>Download start ho raha hai...
    `;

    statusBox.textContent = "Download processing...";

    const response = await fetch("/api/download", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        url: url,
        mode: mode,
        quality: quality
      })
    });

    if (!response.ok) {

      let message = "Download failed.";

      try {
        const data = await response.json();
        message = data.error || message;
      } catch {}

      throw new Error(message);
    }

    const blob = await response.blob();

    const contentDisposition =
      response.headers.get("Content-Disposition") || "";

    let filename =
      mode === "audio"
        ? "rajput-audio.mp3"
        : "rajput-video.mp4";

    const match =
      contentDisposition.match(/filename="?([^"]+)"?/i);

    if (match && match[1]) {
      filename = match[1];
    }

    const downloadUrl =
      URL.createObjectURL(blob);

    const a = document.createElement("a");

    a.href = downloadUrl;
    a.download = filename;

    document.body.appendChild(a);
    a.click();
    a.remove();

    URL.revokeObjectURL(downloadUrl);

    statusBox.textContent =
      "Download complete ✅";

  } catch (error) {

    statusBox.textContent =
      error.message || "Download failed.";

    resultContent.textContent =
      "Kuch problem aa gayi. URL check karo.";

  } finally {

    downloadBtn.disabled = false;
    downloadBtn.textContent = "DOWNLOAD NOW";
  }
});

// SECURITY
function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
