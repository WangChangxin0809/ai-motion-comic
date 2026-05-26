async (page) => {
  // Use the browser to upload the file to ComfyUI
  // Read the file and POST it
  const fs = require("fs");
  const path = require("path");

  const filePath = "D:/0_Study/Python_project/ai-motion-comic/workflows/clip_l.safetensors";
  const fileBuffer = fs.readFileSync(filePath);
  const blob = new Blob([fileBuffer], { type: "application/octet-stream" });

  const formData = new FormData();
  formData.append("image", blob, "clip_l.safetensors");
  formData.append("subfolder", "");
  formData.append("type", "input");

  const resp = await fetch("http://117.50.27.169:8188/api/upload/image", {
    method: "POST",
    body: formData
  });

  return resp.status + ": " + (await resp.text());
}
