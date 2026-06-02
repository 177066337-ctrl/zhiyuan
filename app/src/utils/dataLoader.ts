import type { Major, School } from "../types";

async function loadJson<T>(url: string): Promise<T[]> {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`无法加载数据文件：${url}`);
  }

  const data = await response.json();
  if (!Array.isArray(data)) {
    throw new Error(`数据格式异常：${url}`);
  }
  return data as T[];
}

export async function loadSchools() {
  return loadJson<School>(`${import.meta.env.BASE_URL}data/schools.enriched.json`);
}

export async function loadMajors() {
  return loadJson<Major>(`${import.meta.env.BASE_URL}data/majors.json`);
}
