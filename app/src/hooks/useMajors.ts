import { useEffect, useState } from "react";
import type { DataState, Major } from "../types";
import { loadMajors } from "../utils/dataLoader";

export function useMajors() {
  const [state, setState] = useState<DataState<Major>>({
    data: [],
    loading: true,
    error: null,
  });

  useEffect(() => {
    let active = true;
    loadMajors()
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
