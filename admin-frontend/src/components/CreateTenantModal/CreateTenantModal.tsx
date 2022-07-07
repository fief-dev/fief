import { useCallback, useState } from 'react';
import { FormProvider, SubmitHandler, useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import { useAPI, useAPIErrorHandler } from '../../hooks/api';
import { useFieldRequiredErrorMessage } from '../../hooks/errors';
import * as schemas from '../../schemas';
import ErrorAlert from '../ErrorAlert/ErrorAlert';
import FormErrorMessage from '../FormErrorMessage/FormErrorMessage';
import LoadingButton from '../LoadingButton/LoadingButton';
import Modal from '../Modal/Modal';

interface CreateTenantModalProps {
  open: boolean;
  onClose: () => void;
  onCreated?: (client: schemas.tenant.Tenant) => void;
}

const CreateTenantModal: React.FunctionComponent<React.PropsWithChildren<CreateTenantModalProps>> = ({ open, onClose, onCreated }) => {
  const { t } = useTranslation(['tenants']);
  const api = useAPI();

  const form = useForm<schemas.tenant.TenantCreate>();
  const { register, handleSubmit, reset, setError, formState: { errors } } = form;
  const fieldRequiredErrorMessage = useFieldRequiredErrorMessage();

  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | undefined>();
  const handleAPIError = useAPIErrorHandler(setErrorMessage, setError);

  const onSubmit: SubmitHandler<schemas.tenant.TenantCreate> = useCallback(async (data) => {
    setLoading(true);
    try {
      const { data: client } = await api.createTenant(data);
      if (onCreated) {
        onCreated(client);
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

export default CreateTenantModal;
