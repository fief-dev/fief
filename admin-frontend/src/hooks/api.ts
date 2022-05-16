import { AxiosResponse } from 'axios';
import * as R from 'ramda';
import { useCallback, useContext, useEffect, useState } from 'react';
import { UseFormSetError } from 'react-hook-form';
import { SortingRule } from 'react-table';

import APIClientContext from '../contexts/api';
import { APIClient, handleAPIError } from '../services/api';
import * as schemas from '../schemas';

export const useAPI = (): APIClient => {
  const api = useContext(APIClientContext);
  return api;
};

// eslint-disable-next-line @typescript-eslint/no-unused-vars
type ListMethodKeys<Set> = Set extends `list${infer _X}` ? Set : never;
type APIClientListMethods = Pick<APIClient, ListMethodKeys<keyof APIClient>>;

type Awaited<T> = T extends PromiseLike<infer U> ? U : T;
type ExtractAxiosResponseGeneric<Type> = Type extends AxiosResponse<infer X> ? X : never
type ExtractPaginatedResultsGeneric<Type> = Type extends schemas.PaginatedResults<infer X> ? X : never
type ExtractedDataType<M extends keyof APIClientListMethods> = ExtractPaginatedResultsGeneric<ExtractAxiosResponseGeneric<Awaited<ReturnType<APIClient[M]>>>>;

type UsePaginationAPIProps = { [M in keyof APIClientListMethods]: {
  method: M;
  limit: number;
  filters?: Parameters<APIClient[M]>[0];
  initialPage?: number;
  initialSorting?: SortingRule<ExtractedDataType<M>>[];
  manual?: boolean;
} };

type UsePaginationAPIReturnProps = { [M in keyof APIClientListMethods]: {
  data: ExtractedDataType<M>[];
  count: number;
  refresh: () => void;
  page: number;
  maxPage: number;
  onPageChange: (page: number) => void;
  sorting: SortingRule<ExtractedDataType<M>>[];
  onSortingChange: (sorting: SortingRule<ExtractedDataType<M>>[]) => void;
} };

export const usePaginationAPI = <M extends keyof APIClientListMethods>({ method, limit, filters: _filters, initialPage, initialSorting, manual }: UsePaginationAPIProps[M]): UsePaginationAPIReturnProps[M] => {
  const api = useAPI();
  const [data, setData] = useState<any[]>([]);
  const [count, setCount] = useState(0);
  const [filters, setFilters] = useState<typeof _filters | undefined>(_filters);
  const [page, setPage] = useState(initialPage !== undefined ? initialPage : 1);
  const [maxPage, setMaxPage] = useState(1);
  const [sorting, setSorting] = useState<SortingRule<any>[]>(initialSorting !== undefined ? initialSorting : []);
  const [refreshTrigger, setRefreshTrigger] = useState(false);

  useEffect(() => {
    if (!R.equals(filters, _filters)) {
      setFilters(_filters);
    }
  }, [_filters, filters]);

  const loadData = useCallback(async () => {
    const skip = (page - 1) * limit;
    const { data: paginatedResults } = await api[method]({
      limit,
      skip,
      ...filters ? { ...filters } : {},
      ...sorting.length > 0 ? {
        ordering: sorting.map((rule) => `${rule.desc ? '-' : ''}${rule.id}`).join(','),
      } : {},
    });
    setData(paginatedResults.results);
    setCount(paginatedResults.count);
    setMaxPage(Math.ceil(paginatedResults.count / limit));
    setRefreshTrigger(false);
  }, [api, method, page, limit, filters, sorting]);

  const onPageChange = useCallback((page: number) => {
    setPage(page);
  }, []);

  const onSortingChange = useCallback((sorting: SortingRule<any>[]) => {
    setSorting(sorting);
  }, []);

  const refresh = useCallback(() => {
    setRefreshTrigger(true);
  }, []);

  useEffect(() => {
    if (refreshTrigger) {
      loadData();
    }
  }, [loadData, refreshTrigger]);

  useEffect(() => {
    if (!manual) {
      loadData();
    }
  }, [loadData, manual]);

  return {
    data,
    count,
    refresh,
    page,
    maxPage,
    onPageChange,
    sorting,
    onSortingChange,
  };
};

export const useAPIErrorHandler = (setGlobalMessage: (message: string) => void, setFieldMessage?: UseFormSetError<any>): (err: unknown) => void => {
  return useCallback((err: unknown) => {
    const [globalMessage, fieldsMessages] = handleAPIError(err);
    if (globalMessage) {
      setGlobalMessage(globalMessage);
    }
    if (setFieldMessage) {
      for (const fieldMessage of fieldsMessages) {
        const loc = fieldMessage.loc[0] === 'body' ? fieldMessage.loc.slice(1) : fieldMessage.loc;
        setFieldMessage(loc.join('.'), { message: fieldMessage.msg, type: fieldMessage.type });
      }
    }
  }, [setGlobalMessage, setFieldMessage]);
};
