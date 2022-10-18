import { useCallback, useEffect, useMemo, useState } from 'react';
import { FormProvider, SubmitHandler, useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import { useAPI, useAPIErrorHandler } from '../../hooks/api';
import * as schemas from '../../schemas';
import ClipboardButton from '../ClipboardButton/ClipboardButton';
import DeleteModal from '../DeleteModal/DeleteModal';
import ErrorAlert from '../ErrorAlert/ErrorAlert';
import LoadingButton from '../LoadingButton/LoadingButton';
import OAuthProviderForm from '../OAuthProviderForm/OAuthProviderForm';

interface OAuthProviderDetailsProps {
  oauthProvider: schemas.oauthProvider.OAuthProvider;
  onUpdated?: (client: schemas.oauthProvider.OAuthProvider) => void;
  onDeleted?: () => void;
}

const OAuthProviderDetails: React.FunctionComponent<React.PropsWithChildren<OAuthProviderDetailsProps>> = ({ oauthProvider, onUpdated, onDeleted: _onDeleted }) => {
  const { t } = useTranslation(['oauth-providers']);
  const api = useAPI();

  const defaultValues = useMemo(
    () => ({
      ...oauthProvider,
      client_id: undefined,
      client_secret: undefined,
      scopes: oauthProvider.scopes.map((value) => ({ id: '', value })),
    }),
    [oauthProvider],
  );
  const form = useForm<schemas.oauthProvider.OAuthProviderUpdateForm>({ defaultValues });
  const { handleSubmit, reset, setError } = form;

  useEffect(() => {
    reset(defaultValues);
  }, [reset, defaultValues]);

  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | undefined>();
  const handleAPIError = useAPIErrorHandler(setErrorMessage, setError);

  const onSubmit: SubmitHandler<schemas.oauthProvider.OAuthProviderUpdateForm> = useCallback(async (data) => {
    setLoading(true);
    try {
      const { data: updatedOAuthProvider } = await api.updateOAuthProvider(oauthProvider.id, {
        ...data,
        client_id: data.client_id ? data.client_id : undefined,
        client_secret: data.client_secret ? data.client_secret : undefined,
        scopes: data.scopes !== undefined ? data.scopes.map(({ value }) => value) : undefined,
      });
      if (onUpdated) {
        onUpdated(updatedOAuthProvider);
        reset();
      }
    } catch (err) {
      handleAPIError(err);
    } finally {
      setLoading(false);
    }
  }, [oauthProvider, api, onUpdated, reset, handleAPIError]);

  const [showDeleteModal, setShowDeleteModal] = useState(false);

  const onDeleted = useCallback(() => {
    if (_onDeleted) {
      _onDeleted();
    };
  }, [_onDeleted]);

  return (
    <>
      <div className="text-slate-800 font-semibold text-center mb-6">{t(`available_oauth_provider.${oauthProvider.provider}`)}</div>
      <div className="mt-6">
        <ul>
          <li className="flex items-center justify-between py-3 border-b border-slate-200">
            <div className="text-sm whitespace-nowrap">{t('details.id')}</div>
            <div className="text-sm font-medium text-slate-800 ml-2 truncate">{oauthProvider.id}</div>
            <ClipboardButton text={oauthProvider.id} />
          </li>
        </ul>
      </div>
      <div className="mt-6 pb-6 border-b border-slate-200">
        <FormProvider {...form}>
          <form onSubmit={handleSubmit(onSubmit)}>
            <div className="space-y-4">
              {errorMessage && <ErrorAlert message={t(`common:api_errors.${errorMessage}`)} />}
              <OAuthProviderForm update={true} />
              <LoadingButton
                loading={loading}
                type="submit"
                className="btn w-full border-slate-200 hover:border-slate-300"
              >
                {t('details.submit')}
              </LoadingButton>
            </div>
          </form>
        </FormProvider>
      </div>
      <div className="mt-6">
        <button
          type="button"
          className="btn w-full bg-red-500 hover:bg-red-600 text-white"
          onClick={() => setShowDeleteModal(true)}
        >
          {t('details.delete')}
        </button>
      </div>
      <DeleteModal
        objectId={oauthProvider.id}
        method="deleteOAuthProvider"
        title={t('delete.title', { name: t(`available_oauth_provider.${oauthProvider.provider}`) })}
        notice={t('delete.notice')}
        open={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        onDeleted={onDeleted}
      />
    </>
  );
};

export default OAuthProviderDetails;
