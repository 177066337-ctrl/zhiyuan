export interface School {
  school_id: string;
  school_name: string;
  province: string;
  city: string;
  department: string;
  school_level: string;
  school_type?: string;
  ownership?: string;
  is_985?: boolean;
  is_211?: boolean;
  is_double_first_class?: boolean;
  double_first_class_disciplines?: string[];
  tags?: string[];
  official_site?: string;
  source_file: string;
  source_row: number;
  tag_sources?: string[];
}

export interface Major {
  major_id: string;
  major_code: string;
  major_name: string;
  major_category?: string;
  major_discipline?: string;
  degree_level: string;
  degree?: string;
  duration?: string;
  subject_requirement?: string;
  description?: string;
  source_file: string;
  source_row: number;
}

export interface WishlistItem {
  id: string;
  type: "school" | "major";
  title: string;
  subtitle: string;
  createdAt: string;
}

export interface SchoolFilter {
  keyword: string;
  province: string;
  city: string;
  schoolLevel: string;
  ownership: string;
  schoolType: string;
  tag: string;
}

export interface MajorFilter {
  keyword: string;
  majorCode: string;
  degreeLevel: string;
  majorDiscipline: string;
  majorCategory: string;
}

export interface DataState<T> {
  data: T[];
  loading: boolean;
  error: string | null;
}
