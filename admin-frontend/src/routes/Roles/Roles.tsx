import { CheckIcon, PlusIcon, XMarkIcon } from '@heroicons/react/20/solid';
import { useCallback, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Column } from 'react-table';
import CreateRoleModal from '../../components/CreateRoleModal/CreateRoleModal';

import DataTable from '../../components/DataTable/DataTable';
import Layout from '../../components/Layout/Layout';
import RoleDetails from '../../components/RoleDetails/RoleDetails';
import { usePaginationAPI } from '../../hooks/api';
import * as schemas from '../../schemas';

const Roles: React.FunctionComponent<React.PropsWithChildren<unknown>> = () => {
  const { t } = useTranslation(['roles']);
  const {
    data: roles,
    count,
    page,
    maxPage,
    onPageChange,
    sorting,
    onSortingChange,
    refresh,
  } = usePaginationAPI<'listRoles'>({
    method: 'listRoles',
    limit: 10,
    initialSorting: [{ id: 'name' }],
  });

  const [selected, setSelected] = useState<schemas.role.Role | undefined>();
  const onRoleSelected = useCallback((client: schemas.role.Role) => {
    if (selected && selected.id === client.id) {
      setSelected(undefined);
    } else {
      setSelected(client);
    }
  }, [selected]);

  const [showCreateModal, setShowCreateModal] = useState(false);

  const onCreated = useCallback((role: schemas.role.Role) => {
    setShowCreateModal(false);
    refresh();
    setSelected(role);
  }, [refresh]);

  const onUpdated = useCallback((role: schemas.role.Role) => {
    refresh();
    setSelected(role);
  }, [refresh]);

  const onDeleted = useCallback(() => {
    refresh();
    setSelected(undefined);
  }, [refresh]);

  const columns = useMemo<Column<schemas.role.Role>[]>(() => {
    return [
      {
        Header: t('list.name') as string,
        accessor: 'name',
        Cell: ({ cell: { value }, row: { original } }) => (
          <>
            <span className="font-medium text-slate-800 hover:text-slate-900 cursor-pointer" onClick={() => onRoleSelected(original)}>{value}</span>
          </>
        )
      },
      {
        Header: t('list.granted_by_default') as string,
        accessor: 'granted_by_default',
        Cell: ({ value }) => (
          value ?
            <CheckIcon className="w-4 h-4 fill-current" /> :
            <XMarkIcon className="w-4 h-4 fill-current" />
        ),
      },
    ];
  }, [t, onRoleSelected]);

  return (
    <Layout sidebar={selected ? <RoleDetails role={selected} onUpdated={onUpdated} onDeleted={onDeleted} /> : undefined}>
      <div className="sm:flex sm:justify-between sm:items-center mb-8">

        <div className="mb-4 sm:mb-0">
          <h1 className="text-2xl md:text-3xl text-slate-800 font-bold">{t('list.title')}</h1>
        </div>

        <div className="grid grid-flow-col sm:auto-cols-max justify-start sm:justify-end gap-2">
          <button
            className="btn bg-primary-500 hover:bg-primary-600 text-white"
            onClick={() => setShowCreateModal(true)}
          >
            <PlusIcon width="16" height="16" />
            <span className="hidden xs:block ml-2">{t('list.create')}</span>
          </button>
        </div>

      </div>

      <DataTable
        title={t('list.title')}
        count={count}
        pageSize={10}
        data={roles}
        columns={columns}
        sorting={sorting}
        onSortingChange={onSortingChange}
        page={page}
        maxPage={maxPage}
        onPageChange={onPageChange}
      />

      <CreateRoleModal
        open={showCreateModal}
        onCreated={onCreated}
        onClose={() => setShowCreateModal(false)}
      />
    </Layout>
  );
};

export default Roles;
