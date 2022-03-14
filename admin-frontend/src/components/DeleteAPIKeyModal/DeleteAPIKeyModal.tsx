import { useCallback, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { useAPI } from '../../hooks/api';
import * as schemas from '../../schemas';
import { handleAPIError } from '../../services/api';
import ErrorAlert from '../ErrorAlert/ErrorAlert';
import LoadingButton from '../LoadingButton/LoadingButton';
import Modal from '../Modal/Modal';

interface DeleteAPIKeyModalProps {
  apiKey: schemas.adminAPIKey.AdminAPIKey;
  open: boolean;
  onClose: () => void;
  onDeleted?: () => void;
}

const DeleteAPIKeyModal: React.FunctionComponent<DeleteAPIKeyModalProps> = ({ apiKey, open, onClose, onDeleted }) => {
  const { t } = useTranslation(['api-keys']);
  const api = useAPI();

  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | undefined>();

  const onSubmit = useCallback(async () => {
    setLoading(true);
    try {
      await api.deleteAPIKey(apiKey.id);
      if (onDeleted) {
        onDeleted();
      }
    } catch (err) {
      setErrorMessage(handleAPIError(err));
    } finally {
      setLoading(false);
    }
  }, [api, apiKey, onDeleted]);

  return (
    <Modal
      open={open}
      onClose={onClose}
    >
        <Modal.Header closeButton>
          <Modal.Title>{t('delete.title', { name: apiKey.name })}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <div className="space-y-4">
            {errorMessage && <ErrorAlert message={t(`common:api_errors.${errorMessage}`)} />}
            <p className="text-justify">{t('delete.notice')}</p>
          </div>
        </Modal.Body>
        <Modal.Footer>
          <button
            type="button"
            className="btn-sm border-slate-200 hover:border-slate-300 text-slate-600"
            onClick={() => onClose()}
          >
            {t('delete.cancel')}
          </button>
          <LoadingButton
            loading={loading}
            type="button"
            className="btn-sm bg-red-500 hover:bg-red-600 text-white"
            onClick={() => onSubmit()}
          >
            {t('delete.submit')}
          </LoadingButton>
        </Modal.Footer>
    </Modal>
  );
};

export default DeleteAPIKeyModal;
