import { useCallback, useState } from 'react';
import { FormProvider, SubmitHandler, useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import { useAPI, useAPIErrorHandler } from '../../hooks/api';
import * as schemas from '../../schemas';
import ErrorAlert from '../ErrorAlert/ErrorAlert';
import LoadingButton from '../LoadingButton/LoadingButton';
import Modal from '../Modal/Modal';
import UserFieldForm from '../UserFieldForm/UserFieldForm';

interface CreateUserFieldModalProps {
  open: boolean;
  onClose: () => void;
  onCreated?: (client: schemas.userField.UserField) => void;
}

const CreateUserFieldModal: React.FunctionComponent<React.PropsWithChildren<CreateUserFieldModalProps>> = ({ open, onClose, onCreated }) => {
  const { t } = useTranslation(['user-fields']);
  const api = useAPI();

  const form = useForm<schemas.userField.UserFieldCreate>({
    defaultValues: {
      type: schemas.userField.UserFieldType.STRING,
      configuration: { at_update: true, default: null },
    },
  });
  const { handleSubmit, reset, setError } = form;

  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | undefined>();
  const handleAPIError = useAPIErrorHandler(setErrorMessage, setError);

  const onSubmit: SubmitHandler<schemas.userField.UserFieldCreate> = useCallback(async (data) => {
    setLoading(true);
    try {
      const { data: userField } = await api.createUserField(data);
      if (onCreated) {
        onCreated(userField);
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
              <UserFieldForm update={false} />
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

export default CreateUserFieldModal;
