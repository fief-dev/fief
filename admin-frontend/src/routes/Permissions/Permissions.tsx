import { PlusIcon } from '@heroicons/react/solid';
import { useCallback, useMemo, useState } from 'react';
import { FormProvider, useForm, SubmitHandler } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { Column } from 'react-table';

import DataTable from '../../components/DataTable/DataTable';
import DeleteModal from '../../components/DeleteModal/DeleteModal';
import ErrorAlert from '../../components/ErrorAlert/ErrorAlert';
import Layout from '../../components/Layout/Layout';
import LoadingButton from '../../components/LoadingButton/LoadingButton';
import PermissionForm from '../../components/PermissionForm/PermissionForm';
import { useAPI, useAPIErrorHandler, usePaginationAPI } from '../../hooks/api';
import * as schemas from '../../schemas';

const Permissions: React.FunctionComponent<React.PropsWithChildren<unknown>> = () => {
  const { t } = useTranslation(['permissions']);
  const {
    data: permissions,
    count,
    page,
    maxPage,
    onPageChange,
    sorting,
    onSortingChange,
    refresh,
  } = usePaginationAPI<'listPermissions'>({
    method: 'listPermissions',
    limit: 10,
    initialSorting: [{ id: 'codename' }],
  });

  const [permissionToDelete, setPermissionToDelete] = useState<schemas.permission.Permission | undefined>();
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  const onDelete = useCallback((permission: schemas.permission.Permission) => {
    setPermissionToDelete(permission);
    setShowDeleteModal(true);
  }, []);

  const onDeleted = useCallback(() => {
    setShowDeleteModal(false);
    setPermissionToDelete(undefined);
    refresh();
  }, [refresh]);

  const columns = useMemo<Column<schemas.permission.Permission>[]>(() => {
    return [
      {
        Header: t('list.name') as string,
        accessor: 'name',
      },
      {
        Header: t('list.codename') as string,
        accessor: 'codename',
      },
      {
        id: 'actions',
        disableSortBy: true,
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

  const api = useAPI();
  const form = useForm<schemas.permission.PermissionCreate>();
  const { handleSubmit, setError, setFocus, reset } = form;
  const [errorMessage, setErrorMessage] = useState<string | undefined>();
  const handleAPIError = useAPIErrorHandler(setErrorMessage, setError);
  const [loading, setLoading] = useState(false);
  const onSubmit: SubmitHandler<schemas.permission.PermissionCreate> = async (data) => {
    setLoading(true);
    try {
      await api.createPermission(data);
      refresh();
      setFocus('name');
      reset();
    } catch (err) {
      handleAPIError(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <div className="sm:flex sm:justify-between sm:items-center mb-8">

        <div className="mb-4 sm:mb-0">
          <h1 className="text-2xl md:text-3xl text-slate-800 font-bold">{t('list.title')}</h1>
        </div>

      </div>

      <FormProvider {...form}>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 mb-8">
          {errorMessage && <ErrorAlert message={t(`common:api_errors.${errorMessage}`)} />}
          <div className="flex gap-4">
            <PermissionForm update={false} />
            <div className="">
              <label className="block text-sm font-medium mb-1">&nbsp;</label>
              <LoadingButton
                loading={loading}
                type="submit"
                className="btn bg-primary-500 hover:bg-primary-600 text-white"
              >
                <PlusIcon width="16" height="16" />
                <span className="hidden xs:block ml-2">{t('list.create')}</span>
              </LoadingButton>
            </div>
          </div>
        </form>
      </FormProvider>

      <DataTable
        title={t('list.title')}
        count={count}
        pageSize={10}
        data={permissions}
        columns={columns}
        sorting={sorting}
        onSortingChange={onSortingChange}
        page={page}
        maxPage={maxPage}
        onPageChange={onPageChange}
      />

      {permissionToDelete &&
        <DeleteModal
          objectId={permissionToDelete.id}
          method="deletePermission"
          title={t('delete.title', { name: permissionToDelete.name })}
          notice={t('delete.notice')}
          open={showDeleteModal}
          onClose={() => setShowDeleteModal(false)}
          onDeleted={onDeleted}
        />
      }
    </Layout>
  );
};

export default Permissions;
