import { useCallback, useEffect, useMemo, useState } from 'react';
import { FormProvider, SubmitHandler, useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import { useAPI } from '../../hooks/api';
import { useFieldRequiredErrorMessage } from '../../hooks/errors';
import * as schemas from '../../schemas';
import { handleAPIError } from '../../services/api';
import ErrorAlert from '../ErrorAlert/ErrorAlert';
import FormErrorMessage from '../FormErrorMessage/FormErrorMessage';
import LoadingButton from '../LoadingButton/LoadingButton';
import Modal from '../Modal/Modal';
import RedirectURISInput from '../RedirectURISInput/RedirectURISInput';

interface EditClientModalProps {
  client: schemas.client.Client;
  open: boolean;
  onClose: () => void;
  onUpdated?: (client: schemas.client.Client) => void;
}

const EditClientModal: React.FunctionComponent<EditClientModalProps> = ({ client, open, onClose: _onClose, onUpdated }) => {
  const { t } = useTranslation(['clients']);
  const api = useAPI();

  const defaultValues = useMemo(
    () => ({
      ...client,
      redirect_uris: client.redirect_uris.map((value) => ({ id: '', value })),
    }),
    [client],
  );
  const form = useForm<schemas.client.ClientUpdateForm>({ defaultValues });
  const { register, handleSubmit, watch, reset, formState: { errors } } = form;
  const fieldRequiredErrorMessage = useFieldRequiredErrorMessage();

  const clientType = watch('client_type');

  useEffect(() => {
    reset(defaultValues);
  }, [reset, defaultValues]);

  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | undefined>();

  const onSubmit: SubmitHandler<schemas.client.ClientUpdateForm> = useCallback(async (data) => {
    setLoading(true);
    try {
      const updateData: schemas.client.ClientUpdate = {
        ...data,
        redirect_uris: data.redirect_uris !== undefined ? data.redirect_uris.map(({ value }) => value) : undefined,
      }
      const { data: updatedClient } = await api.updateClient(client.id, updateData);
      if (onUpdated) {
        onUpdated(updatedClient);
        reset();
      }
    } catch (err) {
      const errorMessage = handleAPIError(err);
      setErrorMessage(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [client, api, onUpdated, reset]);

  const onClose = useCallback(() => {
    _onClose();
    reset(defaultValues);
  }, [reset, defaultValues, _onClose])

  return (
    <Modal
      open={open}
      onClose={onClose}
    >
      <FormProvider {...form}>
        <form onSubmit={handleSubmit(onSubmit)}>
          <Modal.Header closeButton>
            <Modal.Title>{t('edit.title', { client: client.name })}</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <div className="space-y-4">
              {errorMessage && <ErrorAlert message={t(`common:api_errors.${errorMessage}`)} />}
              <div>
                <label className="block text-sm font-medium mb-1" htmlFor="name">{t('base.name')}</label>
                <input
                  id="name"
                  className="form-input w-full"
                  type="text"
                  {...register('name', { required: fieldRequiredErrorMessage })}
                />
                <FormErrorMessage errors={errors} name="name" />
              </div>
              <div>
                <label className="flex items-center text-sm font-medium" htmlFor="first_party">
                  <input
                    id="first_party"
                    className="form-checkbox"
                    type="checkbox"
                    {...register('first_party')}
                  />
                  <span className="ml-2">{t('base.first_party')}</span>
                </label>
                <FormErrorMessage errors={errors} name="first_party" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1" htmlFor="client_type">{t('base.client_type')}</label>
                <select
                  id="client_type"
                  className="form-select w-full"
                  {...register('client_type', { required: fieldRequiredErrorMessage })}
                >
                  {Object.values(schemas.client.ClientType).map((type) =>
                    <option key={type} value={type}>{t(`client_type.${type}`)}</option>
                  )}
                </select>
                <FormErrorMessage errors={errors} name="client_type" />
                <div className="text-justify text-xs mt-1">{t(`client_type_details.${clientType}`)}</div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">{t('base.redirect_uris')}</label>
                <RedirectURISInput />
                <FormErrorMessage errors={errors} name="redirect_uris" />
              </div>
            </div>
          </Modal.Body>
          <Modal.Footer>
            <button
              type="button"
              className="btn-sm border-slate-200 hover:border-slate-300 text-slate-600"
              onClick={() => onClose()}
            >
              {t('edit.cancel')}
            </button>
            <LoadingButton
              loading={loading}
              type="submit"
              className="btn-sm bg-primary-500 hover:bg-primary-600 text-white"
            >
              {t('edit.submit')}
            </LoadingButton>

          </Modal.Footer>
        </form>
      </FormProvider>
    </Modal>
  );
};

export default EditClientModal;
