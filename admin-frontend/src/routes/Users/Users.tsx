import { useCallback, useContext, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { CellProps, Column } from 'react-table';
import { PlusIcon } from '@heroicons/react/solid';

import CreateUserModal from '../../components/CreateUserModal/CreateUserModal';
import DataTable from '../../components/DataTable/DataTable';
import Layout from '../../components/Layout/Layout';
import UserDetails from '../../components/UserDetails/UserDetails';
import UserFieldsSelector from '../../components/UserFieldsSelector/UserFieldsSelector';
import UserFieldValue from '../../components/UserFieldValue/UserFieldValue';
import UserFieldsSelectionContext from '../../contexts/user-fields-selection';
import { usePaginationAPI } from '../../hooks/api';
import { useUserFields } from '../../hooks/user-field';
import * as schemas from '../../schemas';

const Users: React.FunctionComponent = () => {
  const { t } = useTranslation(['users']);
  const userFields = useUserFields();
  const [userFieldsSelection] = useContext(UserFieldsSelectionContext);

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

  const [selected, setSelected] = useState<schemas.user.User | undefined>();

  const onUserSelected = useCallback((user: schemas.user.User) => {
    if (selected && selected.id === user.id) {
      setSelected(undefined);
    } else {
      setSelected(user);
    }
  }, [selected]);

  const columns = useMemo<Column<schemas.user.User>[]>(() => {
    return userFieldsSelection.filter(({ enabled }) => enabled).reduce<Column<schemas.user.User>[]>(
      (columns, { id }) => {
        if (id === 'id') {
          return [
            ...columns,
            {
              Header: t('users:list.id') as string,
              accessor: 'id',
            },
          ];
        } else if (id === 'tenant') {
          return [
            ...columns,
            {
              Header: t('users:list.tenant') as string,
              id: 'tenant_id',
              accessor: 'tenant',
              Cell: ({ cell: { value: tenant } }) => (
                <>{tenant.name}</>
              )
            },
          ];
        } else {
          const userField = userFields.find((userField) => userField.slug === id);
          if (userField) {
            return [
              ...columns,
              {
                Header: userField.name,
                id: userField.id,
                accessor: `fields.${userField.slug}` as any,
                disableSortBy: true,
                Cell: (({ cell: { value } }) => (
                  <UserFieldValue userField={userField} value={value} />
                )) as React.FC<React.PropsWithChildren<CellProps<any>>>
              },
            ];
          } else {
            return columns;
          }
        }
      },
      [
        {
          Header: t('users:list.email') as string,
          accessor: 'email',
          Cell: ({ cell: { value }, row: { original } }) => (
            <span className="font-medium text-slate-800 hover:text-slate-900 cursor-pointer" onClick={() => onUserSelected(original)}>{value}</span>
          )
        },
      ],
    );
  }, [t, userFields, userFieldsSelection, onUserSelected]);

  const [showCreateModal, setShowCreateModal] = useState(false);
  const onCreated = useCallback(() => {
    setShowCreateModal(false);
    refresh();
  }, [refresh]);

  const onUpdated = useCallback((user: schemas.user.User) => {
    refresh();
    setSelected(user);
  }, [refresh]);

  return (
    <Layout sidebar={selected ? <UserDetails user={selected} onUpdated={onUpdated} /> : undefined}>
      <div className="sm:flex sm:justify-between sm:items-center mb-8">

        <div className="mb-4 sm:mb-0">
          <h1 className="text-2xl md:text-3xl text-slate-800 font-bold">{t('users:list.title')}</h1>
        </div>

        <div className="grid grid-flow-col sm:auto-cols-max justify-start sm:justify-end gap-2">
          <UserFieldsSelector />
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
