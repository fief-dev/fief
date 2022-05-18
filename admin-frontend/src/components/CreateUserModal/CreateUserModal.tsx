import { AxiosError } from 'axios';
import { useCallback, useEffect, useState } from 'react';
import { SubmitHandler, useForm, FormProvider } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import { useAPI } from '../../hooks/api';
import { useUserFieldsDefaultValues } from '../../hooks/user-field';
import * as schemas from '../../schemas';
import { handleAPIError } from '../../services/api';
import { cleanUserRequestData } from '../../services/user';
import ErrorAlert from '../ErrorAlert/ErrorAlert';
import LoadingButton from '../LoadingButton/LoadingButton';
import Modal from '../Modal/Modal';
import UserForm from '../UserForm/UserForm';

interface CreateUserModalProps {
  open: boolean;
  onClose: () => void;
  onCreated?: (user: schemas.user.User) => void;
}

const CreateUserModal: React.FunctionComponent<CreateUserModalProps> = ({ open, onClose, onCreated }) => {
  const { t } = useTranslation(['users']);
  const api = useAPI();
  const userFieldsDefaultValues = useUserFieldsDefaultValues();

  const form = useForm<schemas.user.UserCreateInternal>({ defaultValues: { fields: userFieldsDefaultValues } });
  const { handleSubmit, setError, reset } = form;

  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | undefined>();

  const onSubmit: SubmitHandler<schemas.user.UserCreateInternal> = useCallback(async (data) => {
    setLoading(true);
    try {
      const { data: user } = await api.createUser(cleanUserRequestData<schemas.user.UserCreateInternal>(data));
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
              <UserForm update={false} />
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
