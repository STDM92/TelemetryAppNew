import { getBootstrapConfig } from "./app/api/bootstrap";
import { mountShell } from "./app/shell/ShellHome";
import "./styles/app.css";

async function main(): Promise<void> {
  const root = document.getElementById("app");
  if (!root) {
    throw new Error("Missing #app root element.");
  }

  const config = await getBootstrapConfig();
  mountShell(root, config);
}

void main();

