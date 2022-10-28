import { useCallback, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Column } from 'react-table';
import { CheckIcon, PlusIcon, XMarkIcon } from '@heroicons/react/20/solid';

import ClipboardButton from '../../components/ClipboardButton/ClipboardButton';
import CreateTenantModal from '../../components/CreateTenantModal/CreateTenantModal';
import DataTable from '../../components/DataTable/DataTable';
import Layout from '../../components/Layout/Layout';
import { usePaginationAPI } from '../../hooks/api';
import * as schemas from '../../schemas';
import { FIEF_INSTANCE } from '../../services/api';
import TenantDetails from '../../components/TenantDetails/TenantDetails';

const Tenants: React.FunctionComponent<React.PropsWithChildren<unknown>> = () => {
  const { t } = useTranslation(['tenants']);
  const {
    data: tenants,
    count,
    page,
    maxPage,
    onPageChange,
    sorting,
    onSortingChange,
    refresh,
  } = usePaginationAPI<'listTenants'>({ method: 'listTenants', limit: 10 });

  const [selected, setSelected] = useState<schemas.tenant.Tenant | undefined>();

  const onTenantSelected = useCallback((tenant: schemas.tenant.Tenant) => {
    if (selected && selected.id === tenant.id) {
      setSelected(undefined);
    } else {
      setSelected(tenant);
    }
  }, [selected]);

  const columns = useMemo<Column<schemas.tenant.Tenant>[]>(() => {
    return [
      {
        Header: t('tenants:list.name') as string,
        accessor: 'name',
        Cell: ({ cell: { value }, row: { original } }) => (
          <>
            <span className="font-medium text-slate-800 hover:text-slate-900 cursor-pointer" onClick={() => onTenantSelected(original)}>{value}</span>
            {original.default &&
              <div className="inline-flex font-medium rounded-full text-center ml-2 px-2.5 py-0.5 bg-green-100 text-green-600">
                {t('tenants:list.default')}
              </div>
            }
          </>
        )
      },
      {
        Header: t('tenants:list.base_url') as string,
        accessor: 'slug',
        Cell: ({ cell: { value }, row: { original } }) => {
          const baseURL = original.default ? FIEF_INSTANCE : `${FIEF_INSTANCE}/${value}`;

          return (
            <span className="flex">
              <span>{baseURL}</span>
              <ClipboardButton text={baseURL} />
            </span>
          );
        }
      },
      {
        Header: t('tenants:list.registration_allowed') as string,
        accessor: 'registration_allowed',
        Cell: ({ cell: { value } }) => {
          return (
            value ?
              <CheckIcon className="w-4 h-4 fill-current" /> :
              <XMarkIcon className="w-4 h-4 fill-current" />
          );
        }
      },
    ];
  }, [t, onTenantSelected]);

  const [showCreateModal, setShowCreateModal] = useState(false);
  const onCreated = useCallback((tenant: schemas.tenant.Tenant) => {
    setShowCreateModal(false);
    onTenantSelected(tenant);
    refresh();
  }, [onTenantSelected, refresh]);

  const onUpdated = useCallback((tenant: schemas.tenant.Tenant) => {
    refresh();
    setSelected(tenant);
  }, [refresh]);

  return (
    <Layout sidebar={selected ? <TenantDetails tenant={selected} onUpdated={onUpdated} /> : undefined}>
      <div className="sm:flex sm:justify-between sm:items-center mb-8">

        <div className="mb-4 sm:mb-0">
          <h1 className="text-2xl md:text-3xl text-slate-800 font-bold">{t('tenants:list.title')}</h1>
        </div>

        <div className="grid grid-flow-col sm:auto-cols-max justify-start sm:justify-end gap-2">
          <button
            className="btn bg-primary-500 hover:bg-primary-600 text-white"
            onClick={() => setShowCreateModal(true)}
          >
            <PlusIcon width="16" height="16" />
            <span className="hidden xs:block ml-2">{t('tenants:list.create')}</span>
          </button>
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

      <CreateTenantModal
        open={showCreateModal}
        onCreated={onCreated}
        onClose={() => setShowCreateModal(false)}
      />
    </Layout>
  );
};

export default Tenants;
