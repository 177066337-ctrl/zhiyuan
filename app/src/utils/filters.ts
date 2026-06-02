import type { Major, MajorFilter, School, SchoolFilter } from "../types";

export function normalizeText(value: string) {
  return value.trim().toLowerCase();
}

function includesText(target: string, keyword: string) {
  if (!keyword) {
    return true;
  }
  return normalizeText(target).includes(normalizeText(keyword));
}

export function getUniqueOptions(values: Array<string | undefined>) {
  return Array.from(
    new Set(values.map((value) => (value ?? "").trim()).filter(Boolean)),
  ).sort((a, b) => a.localeCompare(b, "zh-CN"));
}

export function filterSchools(schools: School[], filter: SchoolFilter) {
  return schools.filter((school) => {
    const inKeyword =
      includesText(school.school_name, filter.keyword) ||
      includesText(school.city, filter.keyword) ||
      includesText(school.province, filter.keyword);
    const inProvince = !filter.province || school.province === filter.province;
    const inCity = !filter.city || school.city === filter.city;
    const inLevel = !filter.schoolLevel || school.school_level === filter.schoolLevel;
    const inOwnership = !filter.ownership || school.ownership === filter.ownership;
    const inType = !filter.schoolType || school.school_type === filter.schoolType;
    const inTag = !filter.tag || Boolean(school.tags?.includes(filter.tag));

    return inKeyword && inProvince && inCity && inLevel && inOwnership && inType && inTag;
  });
}

export function filterMajors(majors: Major[], filter: MajorFilter) {
  return majors.filter((major) => {
    const inKeyword =
      includesText(major.major_name, filter.keyword) ||
      includesText(major.major_discipline ?? "", filter.keyword) ||
      includesText(major.major_category ?? "", filter.keyword);
    const inCode = !filter.majorCode || includesText(major.major_code, filter.majorCode);
    const inLevel = !filter.degreeLevel || major.degree_level === filter.degreeLevel;
    const inDiscipline =
      !filter.majorDiscipline || major.major_discipline === filter.majorDiscipline;
    const inCategory = !filter.majorCategory || major.major_category === filter.majorCategory;

    return inKeyword && inCode && inLevel && inDiscipline && inCategory;
  });
}
