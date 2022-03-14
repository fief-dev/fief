import { useTranslation } from 'react-i18next';

import * as schemas from '../../schemas';
import ClipboardButton from '../ClipboardButton/ClipboardButton';
import Modal from '../Modal/Modal';
import WarningAlert from '../WarningAlert/WarningAlert';

interface APIKeyTokenModalProps {
  apiKey: schemas.adminAPIKey.AdminAPIKeyCreateResponse;
  open: boolean;
  onClose: () => void;
}

const APIKeyTokenModal: React.FunctionComponent<APIKeyTokenModalProps> = ({ apiKey, open, onClose }) => {
  const { t } = useTranslation(['api-keys']);

  return (
    <Modal open={open}>
      <Modal.Header closeButton>
        <Modal.Title>{t('token.title')}</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <WarningAlert message={t('token.shown_once_alert')} />
        <div className="flex justify-end my-2">
          <ClipboardButton text={apiKey.token} />
        </div>
        <pre className="relative overflow-scroll p-1 bg-slate-100 rounded border border-slate-300">
          {apiKey.token}
        </pre>
      </Modal.Body>
      <Modal.Footer>
        <button
          type="button"
          className="btn-sm bg-primary-500 hover:bg-primary-600 text-white"
          onClick={() => onClose()}
        >
          {t('token.close')}
        </button>
      </Modal.Footer>
    </Modal>
  );
};

export default APIKeyTokenModal;
