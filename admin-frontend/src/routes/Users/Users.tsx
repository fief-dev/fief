import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Column } from 'react-table';

import DataTable from '../../components/DataTable/DataTable';
import Layout from '../../components/Layout/Layout';
import { usePaginationAPI } from '../../hooks/api';
import * as schemas from '../../schemas';

const Users: React.FunctionComponent = () => {
  const { t } = useTranslation(['users']);
  const {
    data: users,
    count,
    page,
    maxPage,
    onPageChange,
    sorting,
    onSortingChange,
  } = usePaginationAPI<'listUsers'>({ method: 'listUsers', limit: 10 });

  const columns = useMemo<Column<schemas.user.User>[]>(() => {
    return [
      {
        Header: t('users:list.email') as string,
        accessor: 'email',
      },
      {
        Header: t('users:list.tenant') as string,
        accessor: 'tenant',
        Cell: ({ cell: { value: tenant }}) => (
          <>{tenant.name}</>
        ),
      },
    ];
  }, [t]);

  return (
    <Layout>
      <div className="sm:flex sm:justify-between sm:items-center mb-8">

        <div className="mb-4 sm:mb-0">
          <h1 className="text-2xl md:text-3xl text-slate-800 font-bold">{t('users:list.title')}</h1>
        </div>

      </div>

      <DataTable
        title={t('users:list.title')}
        count={count}
        pageSize={10}
        data={users}
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

export default Users;
