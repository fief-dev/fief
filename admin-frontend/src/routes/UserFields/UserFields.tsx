import { useCallback, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Column } from 'react-table';
import { PlusIcon } from '@heroicons/react/20/solid';

import CreateUserFieldModal from '../../components/CreateUserFieldModal/CreateUserFieldModal';
import DataTable from '../../components/DataTable/DataTable';
import Layout from '../../components/Layout/Layout';
import { usePaginationAPI } from '../../hooks/api';
import * as schemas from '../../schemas';
import UserFieldDetails from '../../components/UserFieldDetails/UserFieldDetails';

const UserFields: React.FunctionComponent<React.PropsWithChildren<unknown>> = () => {
  const { t } = useTranslation(['user-fields']);
  const {
    data: userFields,
    count,
    page,
    maxPage,
    onPageChange,
    sorting,
    onSortingChange,
    refresh,
  } = usePaginationAPI<'listUserFields'>({
    method: 'listUserFields',
    limit: 10,
    initialSorting: [{ id: 'name' }],
  });

  const [selected, setSelected] = useState<schemas.userField.UserField | undefined>();

  const onUserFieldSelected = useCallback((userField: schemas.userField.UserField) => {
    if (selected && selected.id === userField.id) {
      setSelected(undefined);
    } else {
      setSelected(userField);
    }
  }, [selected]);

  const columns = useMemo<Column<schemas.userField.UserField>[]>(() => {
    return [
      {
        Header: t('user-fields:list.name') as string,
        accessor: 'name',
        Cell: ({ cell: { value }, row: { original } }) => (
          <span className="font-medium text-slate-800 hover:text-slate-900 cursor-pointer" onClick={() => onUserFieldSelected(original)}>{value}</span>
        )
      },
      {
        Header: t('user-fields:list.slug') as string,
        accessor: 'slug',
      },
      {
        Header: t('user-fields:list.type') as string,
        accessor: 'type',
        Cell: ({ cell: { value: type } }) => (
          t(`user-fields:user_field_type.${type}`)
        ),
      },
    ];
  }, [t, onUserFieldSelected]);

  const [showCreateModal, setShowCreateModal] = useState(false);
  const onCreated = useCallback((userField: schemas.userField.UserField) => {
    setShowCreateModal(false);
    onUserFieldSelected(userField);
    refresh();
  }, [onUserFieldSelected, refresh]);

  const onUpdated = useCallback((userField: schemas.userField.UserField) => {
    refresh();
    setSelected(userField);
  }, [refresh]);

  const onDeleted = useCallback(() => {
    refresh();
    setSelected(undefined);
  }, [refresh]);

  return (
    <Layout sidebar={selected ? <UserFieldDetails userField={selected} onUpdated={onUpdated} onDeleted={onDeleted} /> : undefined}>
      <div className="sm:flex sm:justify-between sm:items-center mb-8">

        <div className="mb-4 sm:mb-0">
          <h1 className="text-2xl md:text-3xl text-slate-800 font-bold">{t('user-fields:list.title')}</h1>
        </div>

        <div className="grid grid-flow-col sm:auto-cols-max justify-start sm:justify-end gap-2">
          <button
            className="btn bg-primary-500 hover:bg-primary-600 text-white"
            onClick={() => setShowCreateModal(true)}
          >
            <PlusIcon width="16" height="16" />
            <span className="hidden xs:block ml-2">{t('user-fields:list.create')}</span>
          </button>
        </div>

      </div>

      <DataTable
        title={t('user-fields:list.title')}
        count={count}
        pageSize={10}
        data={userFields}
        columns={columns}
        sorting={sorting}
        onSortingChange={onSortingChange}
        page={page}
        maxPage={maxPage}
        onPageChange={onPageChange}
      />

      <CreateUserFieldModal
        open={showCreateModal}
        onCreated={onCreated}
        onClose={() => setShowCreateModal(false)}
      />
    </Layout>
  );
};

export default UserFields;
