import type { WishlistItem } from "../types";

const WISHLIST_KEY = "zhiyuan-wishlist";

function getStorage() {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage;
}

export function readWishlist(): WishlistItem[] {
  try {
    const storage = getStorage();
    if (!storage) {
      return [];
    }
    const raw = storage.getItem(WISHLIST_KEY);
    if (!raw) {
      return [];
    }
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function writeWishlist(items: WishlistItem[]) {
  try {
    const storage = getStorage();
    if (!storage) {
      return false;
    }
    storage.setItem(WISHLIST_KEY, JSON.stringify(items));
    return true;
  } catch {
    return false;
  }
}

export function exportWishlistFile(items: WishlistItem[]) {
  try {
    const blob = new Blob([JSON.stringify(items, null, 2)], {
      type: "application/json;charset=utf-8",
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "wishlist.json";
    anchor.click();
    URL.revokeObjectURL(url);
    return true;
  } catch {
    return false;
  }
}

export async function copyText(text: string) {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch {
    // Fallback below.
  }

  try {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand("copy");
    document.body.removeChild(textarea);
    return true;
  } catch {
    return false;
  }
}
