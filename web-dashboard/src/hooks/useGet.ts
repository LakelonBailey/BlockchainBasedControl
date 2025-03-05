import { useQuery, UseQueryOptions } from "react-query";
import api from "../utils/api";
import qs from "qs";

interface UseGetOptions {
  params?: object;
}
export default function useGet(
  url: string,
  options: UseGetOptions & UseQueryOptions = {}
) {
  const {
    params,
    enabled,
    staleTime = 1000 * 60 * 5,
    refetchOnWindowFocus,
    retry,
  } = options;

  const queryString = qs.stringify(params, { addQueryPrefix: true });
  return useQuery(
    [url, queryString],
    () => api.get(`${url}${queryString}`).then((res) => res.data),
    {
      staleTime,
      enabled,
      refetchOnWindowFocus: (refetchOnWindowFocus ?? false) as boolean,
      retry,
    }
  );
}
