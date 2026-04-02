// Typed access to Telegram.WebApp
// The SDK is loaded via <script> in index.html
export const tg = window.Telegram?.WebApp;

export function getInitData(): string {
  return tg?.initData ?? "";
}

export function getUser() {
  return tg?.initDataUnsafe?.user ?? null;
}
