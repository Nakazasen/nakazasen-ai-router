function generateText() {
  const pairs = [
    ["GEMINI_API_KEY", document.getElementById("gemini").value.trim()],
    ["GROQ_API_KEY", document.getElementById("groq").value.trim()],
    ["OPENROUTER_API_KEY", document.getElementById("openrouter").value.trim()]
  ].filter(([, value]) => value);
  const lines = ["# Provider keys for nakazasen-ai-router. Keep this file outside the repository."];
  for (const [name, value] of pairs) lines.push(`${name}=${value}`);
  return lines.join("\n") + "\n";
}
function setStatus(message) { document.getElementById("status").textContent = message; }
document.getElementById("generateButton").addEventListener("click", () => {
  document.getElementById("output").value = generateText();
  setStatus("Generated locally. Save outside the repository.");
});
document.getElementById("copyButton").addEventListener("click", async () => {
  await navigator.clipboard.writeText(document.getElementById("output").value || generateText());
  setStatus("Copied to clipboard.");
});
document.getElementById("downloadButton").addEventListener("click", () => {
  const blob = new Blob([document.getElementById("output").value || generateText()], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "provider_keys.env";
  a.click();
  URL.revokeObjectURL(url);
  setStatus("Downloaded. Move the file outside this repository if needed.");
});
