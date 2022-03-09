import { AxiosError } from 'axios';
import { useCallback, useEffect, useState } from 'react';
import { Controller, SubmitHandler, useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import { useAPI } from '../../hooks/api';
import { useFieldRequiredErrorMessage } from '../../hooks/errors';
import * as schemas from '../../schemas';
import { handleAPIError } from '../../services/api';
import ErrorAlert from '../ErrorAlert/ErrorAlert';
import FormErrorMessage from '../FormErrorMessage/FormErrorMessage';
import LoadingButton from '../LoadingButton/LoadingButton';
import Modal from '../Modal/Modal';
import Combobox, { ComboboxOption } from '../Combobox/Combobox';

interface CreateUserModalProps {
  open: boolean;
  onClose: () => void;
  onUserCreated?: (user: schemas.user.User) => void;
}

const CreateUserModal: React.FunctionComponent<CreateUserModalProps> = ({ open, onClose, onUserCreated }) => {
  const { t } = useTranslation(['users']);
  const api = useAPI();

  const { register, handleSubmit, control, setValue, setError, reset, formState: { errors } } = useForm<schemas.user.UserCreateInternal>();
  const fieldRequiredErrorMessage = useFieldRequiredErrorMessage();

  const listTenants = useCallback(async (query?: string): Promise<ComboboxOption[]> => {
    const { data: { results } } = await api.listTenants({ ...query ? { query } : {} });
    return results.map((tenant) => ({ value: tenant.id, label: tenant.name }));
  }, [api]);

  const [initialTenants, setInitialTenants] = useState<ComboboxOption[]>([]);
  useEffect(() => {
    listTenants().then((tenants) => {
      setInitialTenants(tenants);
      setValue('tenant_id', tenants[0].value);
    });
  }, [listTenants, setValue]);

  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | undefined>();

  const onSubmit: SubmitHandler<schemas.user.UserCreateInternal> = useCallback(async (data) => {
    setLoading(true);
    try {
      const { data: user } = await api.createUser(data);
      if (onUserCreated) {
        onUserCreated(user);
        reset();
      }
    } catch (err) {
      const errorMessage = handleAPIError(err);
      if (errorMessage === 'USER_CREATE_INVALID_PASSWORD') {
        const reason = (err as AxiosError).response?.data.reason;
        setError('password', { type: 'manual', message: reason });
      }
      setErrorMessage(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [api, onUserCreated, setError, reset]);

  return (
    <Modal
      open={open}
      onClose={onClose}
    >
      <form onSubmit={handleSubmit(onSubmit)}>
        <Modal.Header closeButton>
          <Modal.Title>{t('create.title')}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <div className="space-y-4">
            {errorMessage && <ErrorAlert message={t(`common:api_errors.${errorMessage}`)} />}
            <div>
              <label className="block text-sm font-medium mb-1" htmlFor="email">{t('create.email')}</label>
              <input
                id="email"
                className="form-input w-full"
                type="email"
                {...register('email', { required: fieldRequiredErrorMessage })}
              />
              <FormErrorMessage errors={errors} name="email" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1" htmlFor="password">{t('create.password')}</label>
              <input
                id="password"
                className="form-input w-full"
                type="password"
                {...register('password', { required: fieldRequiredErrorMessage })}
              />
              <FormErrorMessage errors={errors} name="password" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1" htmlFor="tenant_id">{t('create.tenant')}</label>
              <Controller
                name="tenant_id"
                control={control}
                rules={{ required: fieldRequiredErrorMessage }}
                render={({ field: { onChange, value } }) =>
                  <Combobox
                    initialOptions={initialTenants}
                    onChange={onChange}
                    value={value}
                    noOptionLabel={t('create.no_matching_tenant')}
                    onSearch={listTenants}
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
    </Modal>
  );
};

export default CreateUserModal;
