import { useCallback, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Column } from 'react-table';
import { PlusIcon } from '@heroicons/react/solid';

import CreateAPIKeyModal from '../../components/CreateAPIKeyModal/CreateAPIKeyModal';
import DataTable from '../../components/DataTable/DataTable';
import DateTime from '../../components/DateTime/DateTime';
import Layout from '../../components/Layout/Layout';
import { usePaginationAPI } from '../../hooks/api';
import * as schemas from '../../schemas';
import APIKeyTokenModal from '../../components/APIKeyTokenModal/APIKeyTokenModal';
import DeleteModal from '../../components/DeleteModal/DeleteModal';

const APIKeys: React.FunctionComponent<React.PropsWithChildren<unknown>> = () => {
  const { t } = useTranslation(['api-keys']);
  const {
    data: apiKeys,
    count,
    page,
    maxPage,
    onPageChange,
    sorting,
    onSortingChange,
    refresh,
  } = usePaginationAPI<'listAPIKeys'>({
    method: 'listAPIKeys',
    limit: 10,
    initialSorting: [{ id: 'name' }],
  });

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showTokenModal, setShowTokenModal] = useState(false);
  const [createdAPIKey, setCreatedAPIKey] = useState<schemas.adminAPIKey.AdminAPIKeyCreateResponse | undefined>();
  const [apiKeyToDelete, setAPIKeyToDelete] = useState<schemas.adminAPIKey.AdminAPIKey | undefined>();

  const onCreated = useCallback((apiKey: schemas.adminAPIKey.AdminAPIKeyCreateResponse) => {
    setShowCreateModal(false);
    setCreatedAPIKey(apiKey);
    setShowTokenModal(true);
    refresh();
  }, [refresh]);

  const onDelete = useCallback((apiKey: schemas.adminAPIKey.AdminAPIKey) => {
    setAPIKeyToDelete(apiKey);
    setShowDeleteModal(true);
  }, []);

  const onDeleted = useCallback(() => {
    setShowDeleteModal(false);
    setAPIKeyToDelete(undefined);
    refresh();
  }, [refresh]);

  const columns = useMemo<Column<schemas.adminAPIKey.AdminAPIKey>[]>(() => {
    return [
      {
        Header: t('list.name') as string,
        accessor: 'name',
      },
      {
        Header: t('list.created_at') as string,
        accessor: 'created_at',
        Cell: ({ cell: { value } }) => (
          <DateTime datetime={value} displayTime />
        ),
      },
      {
        id: 'actions',
        accessor: 'id',
        Header: t('list.actions') as string,
        Cell: ({ row: { original } }) => (
          <div className="flex justify-end">
            <button
              type="button"
              className="btn-xs bg-red-500 hover:bg-red-600 text-white"
              onClick={() => onDelete(original)}
            >
              {t('list.delete')}
            </button>
          </div>
        ),
      },
    ];
  }, [t, onDelete]);

  return (
    <Layout>
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
        data={apiKeys}
        columns={columns}
        sorting={sorting}
        onSortingChange={onSortingChange}
        page={page}
        maxPage={maxPage}
        onPageChange={onPageChange}
      />

      <CreateAPIKeyModal
        open={showCreateModal}
        onCreated={onCreated}
        onClose={() => setShowCreateModal(false)}
      />

      {apiKeyToDelete &&
        <DeleteModal
          objectId={apiKeyToDelete.id}
          method="deleteAPIKey"
          title={t('delete.title', { name: apiKeyToDelete.name })}
          notice={t('delete.notice')}
          open={showDeleteModal}
          onClose={() => setShowDeleteModal(false)}
          onDeleted={onDeleted}
        />
      }

      {createdAPIKey &&
        <APIKeyTokenModal
          apiKey={createdAPIKey}
          open={showTokenModal}
          onClose={() => setShowTokenModal(false)}
        />
      }
    </Layout>
  );
};

export default APIKeys;
