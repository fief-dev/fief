import { useTranslation } from 'react-i18next';

import * as schemas from '../../schemas';
import ClipboardButton from '../ClipboardButton/ClipboardButton';

interface ClientDetailsProps {
  client: schemas.client.Client;
}

const ClientDetails: React.FunctionComponent<ClientDetailsProps> = ({ client }) => {
  const { t } = useTranslation(['clients']);

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
    </>
  );
};

export default ClientDetails;
