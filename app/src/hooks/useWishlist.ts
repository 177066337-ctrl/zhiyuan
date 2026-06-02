import { useEffect, useMemo, useState } from "react";
import type { Major, School, WishlistItem } from "../types";
import { readWishlist, writeWishlist } from "../utils/storage";

function buildSchoolItem(school: School): WishlistItem {
  return {
    id: school.school_id,
    type: "school",
    title: school.school_name,
    subtitle: [school.province, school.city, school.school_level].filter(Boolean).join(" · "),
    createdAt: new Date().toISOString(),
  };
}

function buildMajorItem(major: Major): WishlistItem {
  return {
    id: major.major_id,
    type: "major",
    title: major.major_name,
    subtitle: [major.major_code, major.degree_level, major.major_discipline]
      .filter(Boolean)
      .join(" · "),
    createdAt: new Date().toISOString(),
  };
}

export function useWishlist() {
  const [items, setItems] = useState<WishlistItem[]>([]);
  const [message, setMessage] = useState("");

  useEffect(() => {
    setItems(readWishlist());
  }, []);

  useEffect(() => {
    function syncWishlist() {
      setItems(readWishlist());
    }

    window.addEventListener("storage", syncWishlist);
    return () => window.removeEventListener("storage", syncWishlist);
  }, []);

  const itemIds = useMemo(() => new Set(items.map((item) => item.id)), [items]);

  function persist(nextItems: WishlistItem[], successMessage: string, failMessage: string) {
    setItems(nextItems);
    const ok = writeWishlist(nextItems);
    setMessage(ok ? successMessage : failMessage);
  }

  function addSchool(school: School) {
    if (itemIds.has(school.school_id)) {
      setMessage("已收藏");
      return false;
    }
    persist(
      [buildSchoolItem(school), ...items],
      "已加入收藏",
      "收藏写入失败，但页面数据未丢失",
    );
    return true;
  }

  function addMajor(major: Major) {
    if (itemIds.has(major.major_id)) {
      setMessage("已收藏");
      return false;
    }
    persist(
      [buildMajorItem(major), ...items],
      "已加入收藏",
      "收藏写入失败，但页面数据未丢失",
    );
    return true;
  }

  function removeItem(id: string) {
    const nextItems = items.filter((item) => item.id !== id);
    persist(nextItems, "已移除收藏", "移除收藏失败");
  }

  function clearAll() {
    persist([], "已清空收藏", "清空收藏失败");
  }

  function isCollected(id: string) {
    return itemIds.has(id);
  }

  return {
    items,
    message,
    addSchool,
    addMajor,
    removeItem,
    clearAll,
    isCollected,
  };
}
