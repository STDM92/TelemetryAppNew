import { getBootstrapConfig } from "./app/api/bootstrap";

async function main() {
  const app = document.getElementById("app");
  if (!app) return;

  const config = await getBootstrapConfig();

  app.innerHTML = `
    <main style="font-family: system-ui, sans-serif; padding: 24px; color: white; background: #111; min-height: 100vh;">
      <h1 style="margin-top: 0;">Driver App</h1>
      <p>Minimal driver shell placeholder.</p>
      <pre style="padding: 12px; background: #1b1b1b; border-radius: 8px;">${JSON.stringify(config, null, 2)}</pre>
    </main>
  `;
}

main().catch((err) => {
  console.error("Driver app startup failed:", err);
});
