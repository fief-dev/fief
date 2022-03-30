import { useCallback, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { useAPI } from '../../hooks/api';
import * as schemas from '../../schemas';
import ClipboardButton from '../ClipboardButton/ClipboardButton';
import LoadingButton from '../LoadingButton/LoadingButton';
import Modal from '../Modal/Modal';
import EditClientModal from '../EditClientModal/EditClientModal';
import WarningAlert from '../WarningAlert/WarningAlert';

interface ClientDetailsProps {
  client: schemas.client.Client;
  onUpdated?: (client: schemas.client.Client) => void;
}

const ClientDetails: React.FunctionComponent<ClientDetailsProps> = ({ client, onUpdated: _onUpdated }) => {
  const { t } = useTranslation(['clients']);
  const api = useAPI();

  const [encryptionKeyLoading, setEncryptionKeyLoading] = useState(false);
  const [encryptionKey, setEncryptionKey] = useState<string | undefined>();
  const [showEncryptionKeyModal, setShowEncryptionKeyModal] = useState(false);

  const generateEncryptionKey = useCallback(async () => {
    setEncryptionKeyLoading(true);
    const { data } = await api.createClientEncryptionKey(client.id);
    setEncryptionKey(JSON.stringify(data, null, 4));
    setShowEncryptionKeyModal(true);
    setEncryptionKeyLoading(false);
  }, [api, client]);

  const [showEditModal, setShowEditModal] = useState(false);
  const onUpdated = useCallback((client: schemas.client.Client) => {
    setShowEditModal(false);
    if (_onUpdated) {
      _onUpdated(client);
    };
  }, [_onUpdated]);

  return (
    <>
      <div className="text-slate-800 font-semibold text-center mb-6">{client.name}</div>
      <div className="mt-6">
        <ul>
          <li className="flex items-center justify-between py-3 border-b border-slate-200">
            <div className="text-sm whitespace-nowrap">{t('details.client_id')}</div>
            <div className="text-sm font-medium text-slate-800 ml-2 truncate">{client.client_id}</div>
            <ClipboardButton text={client.client_id} />
          </li>
          <li className="flex items-center justify-between py-3 border-b border-slate-200">
            <div className="text-sm whitespace-nowrap">{t('details.client_secret')}</div>
            <div className="text-sm font-medium text-slate-800 ml-2 truncate">{client.client_secret}</div>
            <ClipboardButton text={client.client_secret} />
          </li>
        </ul>
      </div>
      <div className="mt-6">
        <div className="text-sm font-semibold text-slate-800">{t('details.redirect_uris')}</div>
        <ul className="mb-3">
          {client.redirect_uris.map((redirectURI) =>
            <li className="flex items-center justify-between py-3 border-b border-slate-200">
              <div className="text-sm whitespace-nowrap truncate">{redirectURI}</div>
            </li>
          )}
        </ul>
        <button
          type="button"
          className="btn w-full border-slate-200 hover:border-slate-300"
          onClick={() => setShowEditModal(true)}
        >
          {t('details.edit')}
        </button>
        <EditClientModal
          client={client}
          open={showEditModal}
          onClose={() => setShowEditModal(false)}
          onUpdated={onUpdated}
        />
      </div>
      <div className="mt-6">
        <div className="text-sm font-semibold text-slate-800">{t('details.id_token_encryption')}</div>
        <div className="pb-4 border-b border-slate-200">
          <div className="flex justify-between text-sm mb-2">
            <div>
              {client.encrypt_jwk === null && t('details.id_token_encryption_disabled')}
              {client.encrypt_jwk !== null && t('details.id_token_encryption_enabled')}
            </div>
          </div>
          <LoadingButton
            loading={encryptionKeyLoading}
            className="btn w-full border-slate-200 hover:border-slate-300"
            onClick={() => generateEncryptionKey()}
          >
            {client.encrypt_jwk === null && t('details.id_token_encryption_generate_key')}
            {client.encrypt_jwk !== null && t('details.id_token_encryption_regenerate_key')}
          </LoadingButton>
          <Modal
            open={showEncryptionKeyModal}
            onClose={() => setShowEncryptionKeyModal(false)}
          >
            <Modal.Body>
              <WarningAlert message={t('details.id_token_encryption_shown_once')} />
              <div className="flex justify-end my-2">
                <ClipboardButton text={encryptionKey as string} />
              </div>
              <pre className="relative overflow-scroll p-1 bg-slate-100 rounded border border-slate-300">
                {encryptionKey}
              </pre>
            </Modal.Body>
            <Modal.Footer>
              <button
                className="btn-sm border-slate-200 hover:border-slate-300 text-slate-600"
                onClick={() => setShowEncryptionKeyModal(false)}
              >
                {t('details.id_token_encryption_close_modal')}
              </button>

            </Modal.Footer>
          </Modal>
        </div>
      </div>
    </>
  );
};

export default ClientDetails;
