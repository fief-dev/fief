import { useCallback, useState } from 'react';
import { FormProvider, SubmitHandler, useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import { useAPI, useAPIErrorHandler } from '../../hooks/api';
import * as schemas from '../../schemas';
import ErrorAlert from '../ErrorAlert/ErrorAlert';
import LoadingButton from '../LoadingButton/LoadingButton';
import Modal from '../Modal/Modal';
import OAuthProviderForm from '../OAuthProviderForm/OAuthProviderForm';

interface CreateOAuthProviderModalProps {
  open: boolean;
  onClose: () => void;
  onCreated?: (client: schemas.oauthProvider.OAuthProvider) => void;
}

const CreateOAuthProviderModal: React.FunctionComponent<React.PropsWithChildren<CreateOAuthProviderModalProps>> = ({ open, onClose, onCreated }) => {
  const { t } = useTranslation(['oauth-providers']);
  const api = useAPI();

  const form = useForm<schemas.oauthProvider.OAuthProviderCreateForm>({
    defaultValues: {
      scopes: [{ id: '', value: '' }],
      authorize_endpoint: null,
      access_token_endpoint: null,
      refresh_token_endpoint: null,
      revoke_token_endpoint: null,
    },
  });
  const { handleSubmit, reset, setError } = form;

  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | undefined>();
  const handleAPIError = useAPIErrorHandler(setErrorMessage, setError);

  const onSubmit: SubmitHandler<schemas.oauthProvider.OAuthProviderCreateForm> = useCallback(async (data) => {
    setLoading(true);
    try {
      const { data: oauthProvider } = await api.createOAuthProvider({
        ...data,
        scopes: data.scopes.map(({ value }) => value),
      });
      if (onCreated) {
        onCreated(oauthProvider);
        reset();
      }
    } catch (err) {
      handleAPIError(err);
    } finally {
      setLoading(false);
    }
  }, [api, onCreated, reset, handleAPIError]);

  return (
    <Modal
      open={open}
      onClose={onClose}
    >
      <FormProvider {...form}>
        <form onSubmit={handleSubmit(onSubmit)}>
          <Modal.Header closeButton>
            <Modal.Title>{t('create.title')}</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <div className="space-y-4">
              {errorMessage && <ErrorAlert message={t(`common:api_errors.${errorMessage}`)} />}
              <OAuthProviderForm update={false} />
            </div>
          </Modal.Body>
          <Modal.Footer>
            <button
              type="button"
              className="btn-sm border-slate-200 hover:border-slate-300 text-slate-600"
              onClick={() => onClose()}
            >
              {t('create.cancel')}
            </button>
            <LoadingButton
              loading={loading}
              type="submit"
              className="btn-sm bg-primary-500 hover:bg-primary-600 text-white"
            >
              {t('create.submit')}
            </LoadingButton>

          </Modal.Footer>
        </form>
      </FormProvider>
    </Modal>
  );
};

export default CreateOAuthProviderModal;
