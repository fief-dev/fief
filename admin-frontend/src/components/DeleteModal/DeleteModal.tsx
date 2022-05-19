import { useCallback, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { useAPI, useAPIErrorHandler } from '../../hooks/api';
import { APIClient } from '../../services/api';
import ErrorAlert from '../ErrorAlert/ErrorAlert';
import LoadingButton from '../LoadingButton/LoadingButton';
import Modal from '../Modal/Modal';

// eslint-disable-next-line @typescript-eslint/no-unused-vars
type ListMethodKeys<Set> = Set extends `delete${infer _X}` ? Set : never;
type APIClientDeleteMethods = Pick<APIClient, ListMethodKeys<keyof APIClient>>;

interface DeleteModalProps {
  objectId: string;
  method: keyof APIClientDeleteMethods;
  title: string;
  notice: string;
  open: boolean;
  onClose: () => void;
  onDeleted?: () => void;
}

const DeleteModal: React.FunctionComponent<React.PropsWithChildren<DeleteModalProps>> = ({ objectId, method, title, notice, open, onClose, onDeleted }) => {
  const { t } = useTranslation(['common']);
  const api = useAPI();

  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | undefined>();
  const handleAPIError = useAPIErrorHandler(setErrorMessage);

  const onSubmit = useCallback(async () => {
    setLoading(true);
    try {
      await api[method](objectId);
      if (onDeleted) {
        onDeleted();
      }
    } catch (err) {
      handleAPIError(err);
    } finally {
      setLoading(false);
    }
  }, [api, method, objectId, onDeleted, handleAPIError]);

  return (
    <Modal
      open={open}
      onClose={onClose}
    >
        <Modal.Header closeButton>
          <Modal.Title>{title}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <div className="space-y-4">
            {errorMessage && <ErrorAlert message={t(`common:api_errors.${errorMessage}`)} />}
            <p className="text-justify">{notice}</p>
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

export default DeleteModal;
