import { ArrowDownIcon, ArrowUpIcon } from '@heroicons/react/solid';
import * as React from 'react';
import { useEffect } from 'react';
import {
  Column,
  ColumnInstance,
  IdType,
  SortingRule,
  TableOptions,
  TableState,
  UseExpandedOptions,
  UseExpandedState,
  UseSortByColumnProps,
  UseSortByOptions,
  UseSortByState,
  useExpanded,
  useSortBy,
  useTable,
} from 'react-table';

import Pagination from '../Pagination/Pagination';

interface DataTableProps<T extends object> {
  title: string;
  count: number;
  pageSize: number;
  data: T[];
  columns: Column<T>[];
  sorting: SortingRule<T>[];
  onSortingChange: (rules: SortingRule<T>[]) => void;
  expanded?: Record<IdType<T>, boolean>;
  onExpandedChange?: (expanded: Record<IdType<T>, boolean>) => void;
  page: number;
  maxPage: number;
  onPageChange: (page: number) => void;
}

interface ColumnInstanceSortBy<D extends object> extends ColumnInstance<D>, UseSortByColumnProps<D> { }

interface TableStateSortByExpanded<D extends object> extends TableState<D>, UseSortByState<D>, UseExpandedState<D> { }

interface TableOptionsSortByExpanded<D extends object> extends TableOptions<D>, UseSortByOptions<D>, UseExpandedOptions<D> {
  initialState?: TableStateSortByExpanded<D>;
}

const DataTable = <T extends object,>({ title, count, pageSize, data, columns, sorting, onSortingChange, expanded, onExpandedChange, page, maxPage, onPageChange }: DataTableProps<T>) => {
  const options: TableOptionsSortByExpanded<T> = {
    columns,
    data,
    initialState: {
      sortBy: sorting,
      expanded: expanded || {} as Record<IdType<T>, boolean>,
    },
    manualSortBy: true,
  };
  const tableInstance = useTable<T>(options, useSortBy, useExpanded);
  const {
    getTableProps,
    getTableBodyProps,
    headerGroups,
    rows,
    prepareRow,
  } = tableInstance;

  const state = tableInstance.state as TableStateSortByExpanded<T>;

  useEffect(() => {
    onSortingChange(state.sortBy);
  }, [onSortingChange, state]);

  useEffect(() => {
    if (onExpandedChange) {
      onExpandedChange(state.expanded);
    }
  }, [onExpandedChange, state]);

  return (
    <>
      <div className="bg-white shadow-lg rounded-sm border border-slate-200 relative">
        <header className="px-5 py-4">
          <h2 className="font-semibold text-slate-800">{title} <span className="text-slate-400 font-medium">{count}</span></h2>
        </header>

        <div>
          <div className="overflow-x-auto">
            <table {...getTableProps()} className="table-auto w-full">
              <thead className="text-xs font-semibold uppercase text-slate-500 bg-slate-50 border-t border-b border-slate-200">
                {headerGroups.map(headerGroup => (
                  <tr {...headerGroup.getHeaderGroupProps()}>
                    {headerGroup.headers.map(column => (
                      <th {...column.getHeaderProps()} {...column.getHeaderProps((column as unknown as ColumnInstanceSortBy<T>).getSortByToggleProps())} className="px-2 first:pl-5 last:pr-5 py-3 whitespace-nowrap">
                        <div className="font-semibold text-left flex flex-row items-center">
                          {column.render('Header')}
                          <span className="ml-1 w-[8px]">
                            {(column as unknown as ColumnInstanceSortBy<T>).isSorted &&
                              <>
                                {(column as unknown as ColumnInstanceSortBy<T>).isSortedDesc &&
                                  <ArrowDownIcon width={8} height={8} className="fill-current" />
                                }
                                {!(column as unknown as ColumnInstanceSortBy<T>).isSortedDesc &&
                                  <ArrowUpIcon width={8} height={8} className="fill-current" />
                                }
                              </>
                            }
                          </span>
                        </div>
                      </th>
                    ))}
                  </tr>
                ))}
              </thead>
              <tbody {...getTableBodyProps()} className="text-sm divide-y divide-slate-200">
                {rows.map((row) => {
                  prepareRow(row);
                  return (
                    <React.Fragment key={row.id}>
                      <tr {...row.getRowProps()}>
                        {row.cells.map((cell) => {
                          return <td {...cell.getCellProps()} className="px-2 first:pl-5 last:pr-5 py-3 whitespace-nowrap">{cell.render('Cell')}</td>;
                        })}
                      </tr>
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
      <div className="mt-8">
        <Pagination current={page} max={maxPage} pageSize={pageSize} count={count} onPageChanged={onPageChange} />
      </div>
    </>
  );
};

export default DataTable;
