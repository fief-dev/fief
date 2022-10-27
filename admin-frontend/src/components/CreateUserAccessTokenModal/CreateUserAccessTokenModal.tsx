import { useCallback, useState } from 'react';
import { Controller, FormProvider, SubmitHandler, useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import { useAPI, useAPIErrorHandler } from '../../hooks/api';
import { useFieldRequiredErrorMessage } from '../../hooks/errors';
import * as schemas from '../../schemas';
import ClientCombobox from '../ClientCombobox/ClientCombobox';
import ClipboardButton from '../ClipboardButton/ClipboardButton';
import ErrorAlert from '../ErrorAlert/ErrorAlert';
import FormErrorMessage from '../FormErrorMessage/FormErrorMessage';
import LoadingButton from '../LoadingButton/LoadingButton';
import Modal from '../Modal/Modal';
import ScopesInput from '../ScopesInput/ScopesInput';
import WarningAlert from '../WarningAlert/WarningAlert';

interface CreateUserAccessTokenModalProps {
  open: boolean;
  user: schemas.user.User;
  onClose: () => void;
}

const CreateUserAccessTokenModal: React.FunctionComponent<React.PropsWithChildren<CreateUserAccessTokenModalProps>> = ({ open, user, onClose: _onClose }) => {
  const { t } = useTranslation(['users']);
  const api = useAPI();

  const form = useForm<schemas.user.CreateAccessTokenForm>({ defaultValues: { scopes: [{ id: 'openid', value: 'openid' }] } });
  const { control, handleSubmit, reset, setError, formState: { errors } } = form;
  const fieldRequiredErrorMessage = useFieldRequiredErrorMessage();

  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | undefined>();
  const handleAPIError = useAPIErrorHandler(setErrorMessage, setError);

  const [accessTokenResponse, setAccessTokenResponse] = useState<schemas.user.AccessTokenResponse | undefined>();

  const onSubmit: SubmitHandler<schemas.user.CreateAccessTokenForm> = useCallback(async (data) => {
    setLoading(true);
    try {
      const { data: accessTokenResponse } = await api.createUserAccessToken(
        user.id,
        { ...data, scopes: data.scopes.map(({ value }) => value) },
      );
      setAccessTokenResponse(accessTokenResponse);
    } catch (err) {
      handleAPIError(err);
    } finally {
      setLoading(false);
    }
  }, [api, user, handleAPIError]);

  const onClose = useCallback(() => {
    reset();
    setAccessTokenResponse(undefined);
    _onClose();
  }, [reset, _onClose]);

  return (
    <Modal
      open={open}
      onClose={onClose}
    >
      <FormProvider {...form}>
        <form onSubmit={handleSubmit(onSubmit)}>
          <Modal.Header closeButton>
            <Modal.Title>{t('create_access_token.title')}</Modal.Title>
          </Modal.Header>
          {!accessTokenResponse &&
            <>
              <Modal.Body>
                <div className="space-y-4">
                  {errorMessage && <ErrorAlert message={t(`common:api_errors.${errorMessage}`)} />}
                  <div>
                    <label className="block text-sm font-medium mb-1" htmlFor="client_id">{t('create_access_token.client')}</label>
                    <Controller
                      name="client_id"
                      control={control}
                      rules={{ required: fieldRequiredErrorMessage }}
                      render={({ field: { onChange, value } }) =>
                        <ClientCombobox
                          onChange={onChange}
                          value={value}
                        />
                      }
                    />
                    <FormErrorMessage errors={errors} name="client_id" />
                    <div className="text-justify text-xs mt-1">{t('create_access_token.client_details')}</div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1" htmlFor="scope">{t('create_access_token.scopes')}</label>
                    <ScopesInput />
                  </div>
                </div>
              </Modal.Body>
              <Modal.Footer>
                <button
                  type="button"
                  className="btn-sm border-slate-200 hover:border-slate-300 text-slate-600"
                  onClick={() => onClose()}
                >
                  {t('create_access_token.cancel')}
                </button>
                <LoadingButton
                  loading={loading}
                  type="submit"
                  className="btn-sm bg-primary-500 hover:bg-primary-600 text-white"
                >
                  {t('create_access_token.submit')}
                </LoadingButton>

              </Modal.Footer>
            </>
          }
          {accessTokenResponse &&
            <>
              <Modal.Body>
                <WarningAlert message={t('create_access_token.sensitive_alert')} />
                <div className="flex justify-end my-2">
                  <ClipboardButton text={accessTokenResponse.access_token} />
                </div>
                <pre className="relative overflow-scroll p-1 bg-slate-100 rounded border border-slate-300">
                  {accessTokenResponse.access_token}
                </pre>
                <div className="text-justify text-xs mt-1">{t('create_access_token.access_token_expires_in', { expires_in: accessTokenResponse.expires_in })}</div>
              </Modal.Body>
              <Modal.Footer>
                <button
                  type="button"
                  className="btn-sm border-slate-200 hover:border-slate-300 text-slate-600"
                  onClick={() => onClose()}
                >
                  {t('create_access_token.close')}
                </button>
              </Modal.Footer>
            </>
          }
        </form>
      </FormProvider>
    </Modal >
  );
};

export default CreateUserAccessTokenModal;
