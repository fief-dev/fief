import { AxiosError } from 'axios';
import { useCallback, useEffect, useState } from 'react';
import { Controller, SubmitHandler, useForm, FormProvider } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import { useAPI } from '../../hooks/api';
import { useFieldRequiredErrorMessage } from '../../hooks/errors';
import { useUserFields, useUserFieldsDefaultValues } from '../../hooks/user-field';
import * as schemas from '../../schemas';
import { handleAPIError } from '../../services/api';
import ErrorAlert from '../ErrorAlert/ErrorAlert';
import FormErrorMessage from '../FormErrorMessage/FormErrorMessage';
import LoadingButton from '../LoadingButton/LoadingButton';
import Modal from '../Modal/Modal';
import TenantCombobox from '../TenantCombobox/TenantCombobox';
import UserFieldInput from '../UserFieldInput/UserFieldInput';

interface CreateUserModalProps {
  open: boolean;
  onClose: () => void;
  onCreated?: (user: schemas.user.User) => void;
}

const CreateUserModal: React.FunctionComponent<CreateUserModalProps> = ({ open, onClose, onCreated }) => {
  const { t } = useTranslation(['users']);
  const api = useAPI();
  const userFields = useUserFields();
  const userFieldsDefaultValues = useUserFieldsDefaultValues();

  const form = useForm<schemas.user.UserCreateInternal>({ defaultValues: { fields: userFieldsDefaultValues } });
  const { register, handleSubmit, control, setError, reset, formState: { errors } } = form;
  const fieldRequiredErrorMessage = useFieldRequiredErrorMessage();

  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | undefined>();

  const onSubmit: SubmitHandler<schemas.user.UserCreateInternal> = useCallback(async (data) => {
    setLoading(true);
    try {
      const { data: user } = await api.createUser(data);
      if (onCreated) {
        onCreated(user);
        reset();
      }
    } catch (err) {
      const [globalMessage, fieldsMessages] = handleAPIError(err);
      if (globalMessage === 'USER_CREATE_INVALID_PASSWORD') {
        const reason = (err as AxiosError).response?.data.reason;
        setError('password', { type: 'manual', message: reason });
      }
      for (const fieldMessage of fieldsMessages) {
        const loc = fieldMessage.loc[0] === 'body' ? fieldMessage.loc.slice(1) : fieldMessage.loc;
        setError(loc.join('.') as any, { message: fieldMessage.msg, type: fieldMessage.type });
      }
      setErrorMessage(globalMessage);
    } finally {
      setLoading(false);
      setErrorMessage(undefined);
    }
  }, [api, onCreated, setError, reset]);

  useEffect(() => {
    reset({ fields: userFieldsDefaultValues });
  }, [reset, userFieldsDefaultValues]);

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
                    <TenantCombobox
                      onChange={onChange}
                      value={value}
                    />
                  }
                />
                <FormErrorMessage errors={errors} name="tenant_id" />
              </div>
              {userFields.map((userField) =>
                <div key={userField.slug}>
                  <UserFieldInput userField={userField} path="fields" />
                </div>
              )}
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

export default CreateUserModal;
