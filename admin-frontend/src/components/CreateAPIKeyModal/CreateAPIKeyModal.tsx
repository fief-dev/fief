import { useCallback, useState } from 'react';
import { SubmitHandler, useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import { useAPI, useAPIErrorHandler } from '../../hooks/api';
import { useFieldRequiredErrorMessage } from '../../hooks/errors';
import * as schemas from '../../schemas';
import ErrorAlert from '../ErrorAlert/ErrorAlert';
import FormErrorMessage from '../FormErrorMessage/FormErrorMessage';
import LoadingButton from '../LoadingButton/LoadingButton';
import Modal from '../Modal/Modal';

interface CreateAPIKeyModalProps {
  open: boolean;
  onClose: () => void;
  onCreated?: (user: schemas.adminAPIKey.AdminAPIKeyCreateResponse) => void;
}

const CreateAPIKeyModal: React.FunctionComponent<CreateAPIKeyModalProps> = ({ open, onClose, onCreated }) => {
  const { t } = useTranslation(['api-keys']);
  const api = useAPI();

  const { register, handleSubmit, reset, setError, formState: { errors } } = useForm<schemas.adminAPIKey.AdminAPIKeyCreate>();
  const fieldRequiredErrorMessage = useFieldRequiredErrorMessage();

  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | undefined>();
  const handleAPIError = useAPIErrorHandler(setErrorMessage, setError);

  const onSubmit: SubmitHandler<schemas.adminAPIKey.AdminAPIKeyCreate> = useCallback(async (data) => {
    setLoading(true);
    try {
      const { data: apiKey } = await api.createAPIKey(data);
      if (onCreated) {
        onCreated(apiKey);
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

export default CreateAPIKeyModal;
