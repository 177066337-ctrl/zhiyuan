import { useEffect, useState } from "react";
import type { DataState, School } from "../types";
import { loadSchools } from "../utils/dataLoader";

export function useSchools() {
  const [state, setState] = useState<DataState<School>>({
    data: [],
    loading: true,
    error: null,
  });

  useEffect(() => {
    let active = true;
    loadSchools()
      .then((data) => {
        if (!active) {
          return;
        }
        setState({ data, loading: false, error: null });
      })
      .catch((error: Error) => {
        if (!active) {
          return;
        }
        setState({ data: [], loading: false, error: error.message });
      });

    return () => {
      active = false;
    };
  }, []);

  return state;
}
