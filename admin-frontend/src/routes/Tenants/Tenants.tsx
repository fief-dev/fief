import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Column } from 'react-table';

import DataTable from '../../components/DataTable/DataTable';
import Layout from '../../components/Layout/Layout';
import Pagination from '../../components/Pagination/Pagination';
import { usePaginationAPI } from '../../hooks/api';
import * as schemas from '../../schemas';

const Tenants: React.FunctionComponent = () => {
  const { t } = useTranslation(['tenants']);
  const {
    data: tenants,
    count,
    page,
    maxPage,
    onPageChange,
    sorting,
    onSortingChange,
  } = usePaginationAPI<'listTenants'>({ method: 'listTenants', limit: 10 });

  const columns = useMemo<Column<schemas.tenant.Tenant>[]>(() => {
    return [
      {
        Header: t('tenants:list.name') as string,
        accessor: 'name',
        Cell: ({ cell: { value }, row: { original } }) => (
          <>
            {value}
            {original.default &&
              <div className="inline-flex font-medium rounded-full text-center ml-2 px-2.5 py-0.5 bg-green-100 text-green-600">
                {t('tenants:list.default')}
              </div>
            }
          </>
        )
      },
      {
        Header: t('tenants:list.path') as string,
        accessor: 'slug',
        Cell: ({ cell: { value }, row: { original } }) => (
          <>
            {original.default ? '/' : `/${value}`}
          </>
        )
      },
    ];
  }, [t]);

  return (
    <Layout>
      <div className="sm:flex sm:justify-between sm:items-center mb-8">

        {/* Left: Title */}
        <div className="mb-4 sm:mb-0">
          <h1 className="text-2xl md:text-3xl text-slate-800 font-bold">{t('tenants:list.title')}</h1>
        </div>

      </div>

      <DataTable
        title={t('tenants:list.title')}
        count={count}
        pageSize={10}
        data={tenants}
        columns={columns}
        sorting={sorting}
        onSortingChange={onSortingChange}
        page={page}
        maxPage={maxPage}
        onPageChange={onPageChange}
      />
    </Layout>
  );
};

export default Tenants;
