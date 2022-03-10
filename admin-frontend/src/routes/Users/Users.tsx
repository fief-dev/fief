import { useCallback, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Column } from 'react-table';
import { PlusIcon } from '@heroicons/react/solid';


import CreateUserModal from '../../components/CreateUserModal/CreateUserModal';
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
    refresh,
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
        Cell: ({ cell: { value: tenant } }) => (
          <>{tenant.name}</>
        ),
      },
    ];
  }, [t]);

  const [showCreateModal, setShowCreateModal] = useState(false);
  const onCreated = useCallback(() => {
    setShowCreateModal(false);
    refresh();
  }, [refresh]);

  return (
    <Layout>
      <div className="sm:flex sm:justify-between sm:items-center mb-8">

        <div className="mb-4 sm:mb-0">
          <h1 className="text-2xl md:text-3xl text-slate-800 font-bold">{t('users:list.title')}</h1>
        </div>

        <div className="grid grid-flow-col sm:auto-cols-max justify-start sm:justify-end gap-2">
          <button
            className="btn bg-primary-500 hover:bg-primary-600 text-white"
            onClick={() => setShowCreateModal(true)}
          >
            <PlusIcon width="16" height="16" />
            <span className="hidden xs:block ml-2">{t('users:list.create')}</span>
          </button>
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

      <CreateUserModal
        open={showCreateModal}
        onCreated={onCreated}
        onClose={() => setShowCreateModal(false)}
      />
    </Layout>
  );
};

export default Users;
