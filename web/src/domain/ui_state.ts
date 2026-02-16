export const UI_SELECTED_ACTOR_KEY = "incremental_ui:selected_actor";

export function getSelectedActorIndex(defaultValue = 0): number {
  if (typeof window === "undefined" || !window.localStorage) return defaultValue;
  const raw = window.localStorage.getItem(UI_SELECTED_ACTOR_KEY);
  if (!raw) return defaultValue;
  const parsed = Number(raw);
  return Number.isFinite(parsed) ? parsed : defaultValue;
}

export function setSelectedActorIndex(value: number): void {
  if (typeof window === "undefined" || !window.localStorage) return;
  window.localStorage.setItem(UI_SELECTED_ACTOR_KEY, String(value));
}
