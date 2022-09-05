import { useCallback, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Column } from 'react-table';
import { PlusIcon } from '@heroicons/react/20/solid';

import CreateOAuthProviderModal from '../../components/CreateOAuthProviderModal/CreateOAuthProviderModal';
import DataTable from '../../components/DataTable/DataTable';
import Layout from '../../components/Layout/Layout';
import { usePaginationAPI } from '../../hooks/api';
import * as schemas from '../../schemas';
import OAuthProviderDetails from '../../components/OAuthProviderDetails/OAuthProviderDetails';

const OAuthProviders: React.FunctionComponent<React.PropsWithChildren<unknown>> = () => {
  const { t } = useTranslation(['oauth-providers']);
  const {
    data: oauthProviders,
    count,
    page,
    maxPage,
    onPageChange,
    sorting,
    onSortingChange,
    refresh,
  } = usePaginationAPI<'listOAuthProviders'>({ method: 'listOAuthProviders', limit: 10 });

  const [selected, setSelected] = useState<schemas.oauthProvider.OAuthProvider | undefined>();

  const onOAuthProviderSelected = useCallback((oauthProvider: schemas.oauthProvider.OAuthProvider) => {
    if (selected && selected.id === oauthProvider.id) {
      setSelected(undefined);
    } else {
      setSelected(oauthProvider);
    }
  }, [selected]);

  const columns = useMemo<Column<schemas.oauthProvider.OAuthProvider>[]>(() => {
    return [
      {
        Header: t('oauth-providers:list.provider') as string,
        accessor: 'provider',
        Cell: ({ cell: { value }, row: { original } }) => (
          <span className="font-medium text-slate-800 hover:text-slate-900 cursor-pointer" onClick={() => onOAuthProviderSelected(original)}>{t(`available_oauth_provider.${value}`)}</span>
        ),
      },
      {
        Header: t('oauth-providers:list.name') as string,
        accessor: 'name',
      },
    ];
  }, [t, onOAuthProviderSelected]);

  const [showCreateModal, setShowCreateModal] = useState(false);
  const onCreated = useCallback((oauthProvider: schemas.oauthProvider.OAuthProvider) => {
    setShowCreateModal(false);
    onOAuthProviderSelected(oauthProvider);
    refresh();
  }, [onOAuthProviderSelected, refresh]);

  const onUpdated = useCallback((oauthProvider: schemas.oauthProvider.OAuthProvider) => {
    refresh();
    setSelected(oauthProvider);
  }, [refresh]);

  const onDeleted = useCallback(() => {
    refresh();
    setSelected(undefined);
  }, [refresh]);

  return (
    <Layout sidebar={selected ? <OAuthProviderDetails oauthProvider={selected} onUpdated={onUpdated} onDeleted={onDeleted} /> : undefined}>
      <div className="sm:flex sm:justify-between sm:items-center mb-8">

        <div className="mb-4 sm:mb-0">
          <h1 className="text-2xl md:text-3xl text-slate-800 font-bold">{t('oauth-providers:list.title')}</h1>
        </div>

        <div className="grid grid-flow-col sm:auto-cols-max justify-start sm:justify-end gap-2">
          <button
            className="btn bg-primary-500 hover:bg-primary-600 text-white"
            onClick={() => setShowCreateModal(true)}
          >
            <PlusIcon width="16" height="16" />
            <span className="hidden xs:block ml-2">{t('oauth-providers:list.create')}</span>
          </button>
        </div>

      </div>

      <DataTable
        title={t('oauth-providers:list.title')}
        count={count}
        pageSize={10}
        data={oauthProviders}
        columns={columns}
        sorting={sorting}
        onSortingChange={onSortingChange}
        page={page}
        maxPage={maxPage}
        onPageChange={onPageChange}
      />


      <CreateOAuthProviderModal
        open={showCreateModal}
        onCreated={onCreated}
        onClose={() => setShowCreateModal(false)}
      />
    </Layout>
  );
};

export default OAuthProviders;
