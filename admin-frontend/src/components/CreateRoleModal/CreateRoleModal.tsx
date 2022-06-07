import { useCallback, useState } from 'react';
import { SubmitHandler, useForm, FormProvider } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import { useAPI, useAPIErrorHandler } from '../../hooks/api';
import * as schemas from '../../schemas';
import ErrorAlert from '../ErrorAlert/ErrorAlert';
import LoadingButton from '../LoadingButton/LoadingButton';
import Modal from '../Modal/Modal';
import RoleForm from '../RoleForm/RoleForm';

interface CreateRoleModalProps {
  open: boolean;
  onClose: () => void;
  onCreated?: (role: schemas.role.Role) => void;
}

const CreateRoleModal: React.FunctionComponent<React.PropsWithChildren<CreateRoleModalProps>> = ({ open, onClose, onCreated }) => {
  const { t } = useTranslation(['roles']);
  const api = useAPI();

  const form = useForm<schemas.role.RoleCreate>({ defaultValues: { permissions: [] } });
  const { handleSubmit, setError, reset } = form;

  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | undefined>();
  const handleAPIError = useAPIErrorHandler(setErrorMessage, setError);

  const onSubmit: SubmitHandler<schemas.role.RoleCreate> = useCallback(async (data) => {
    setLoading(true);
    setErrorMessage(undefined);
    try {
      const { data: role } = await api.createRole(data);
      if (onCreated) {
        onCreated(role);
        reset();
      }
    } catch (err) {
      handleAPIError(err);
    } finally {
      setLoading(false);
    }
  }, [api, onCreated, handleAPIError, reset]);

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
              <RoleForm update={false} />
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

export default CreateRoleModal;
