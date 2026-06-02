export function fallbackText(value?: string | null, emptyText = "暂无数据") {
  const text = value?.trim();
  return text ? text : emptyText;
}

export function joinWithSeparator(values: Array<string | undefined>, separator = " · ") {
  return values.filter((value): value is string => Boolean(value && value.trim())).join(separator);
}

export function formatCategory(value?: string | null, fallback = "待细分") {
  const text = value?.trim();
  if (!text || text === "其他") {
    return fallback;
  }
  return text;
}

export function formatList(items?: string[], emptyText = "暂无数据") {
  if (!items || items.length === 0) {
    return emptyText;
  }
  return items.join("、");
}
