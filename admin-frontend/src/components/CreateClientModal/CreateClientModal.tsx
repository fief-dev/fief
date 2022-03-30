import { useCallback, useState } from 'react';
import { Controller, FormProvider, SubmitHandler, useFieldArray, useForm } from 'react-hook-form';
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
import TenantCombobox from '../TenantCombobox/TenantCombobox';

interface CreateClientModalProps {
  open: boolean;
  onClose: () => void;
  onCreated?: (client: schemas.client.Client) => void;
}

const CreateClientModal: React.FunctionComponent<CreateClientModalProps> = ({ open, onClose, onCreated }) => {
  const { t } = useTranslation(['clients']);
  const api = useAPI();

  const form = useForm<schemas.client.ClientCreateForm>({ defaultValues: { redirect_uris: [{ id: '', value: '' }] } });
  const { register, handleSubmit, control, reset, formState: { errors } } = form;
  const fieldRequiredErrorMessage = useFieldRequiredErrorMessage();

  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | undefined>();

  const onSubmit: SubmitHandler<schemas.client.ClientCreateForm> = useCallback(async (data) => {
    setLoading(true);
    try {
      const createData: schemas.client.ClientCreate = {
        ...data,
        redirect_uris: data.redirect_uris.map(({ value }) => value),
      }
      const { data: client } = await api.createClient(createData);
      if (onCreated) {
        onCreated(client);
        reset();
      }
    } catch (err) {
      const errorMessage = handleAPIError(err);
      setErrorMessage(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [api, onCreated, reset]);

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
                <label className="block text-sm font-medium mb-1" htmlFor="name">{t('create.name')}</label>
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
                  <span className="ml-2">{t('create.first_party')}</span>
                </label>
                <FormErrorMessage errors={errors} name="first_party" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">{t('create.redirect_uris')}</label>
                <RedirectURISInput />
                <FormErrorMessage errors={errors} name="redirect_uris" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1" htmlFor="tenant_id">{t('create.tenant')}</label>
                <Controller
                  name="tenant_id"
                  control={control}
                  rules={{ minLength: 1 }}
                  render={({ field: { onChange, value } }) =>
                    <TenantCombobox
                      onChange={onChange}
                      value={value}
                    />
                  }
                />
                <FormErrorMessage errors={errors} name="tenant_id" />
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

export default CreateClientModal;
