import { invoke } from "@tauri-apps/api/core";

type RustPingPayload = {
  app: string;
  message: string;
};

async function pingRust() {
  const statusEl = document.querySelector<HTMLElement>("#rust-status");
  const messageEl = document.querySelector<HTMLElement>("#rust-message");

  if (!statusEl || !messageEl) {
    return;
  }

  statusEl.textContent = "调用中...";
  messageEl.textContent = "正在等待 Rust 后端响应。";

  try {
    const payload = await invoke<RustPingPayload>("ping_rust");
    statusEl.textContent = payload.app;
    messageEl.textContent = payload.message;
  } catch (error) {
    statusEl.textContent = "调用失败";
    messageEl.textContent =
      error instanceof Error ? error.message : String(error);
  }
}

window.addEventListener("DOMContentLoaded", () => {
  document
    .querySelector("#ping-rust-btn")
    ?.addEventListener("click", () => void pingRust());
});
