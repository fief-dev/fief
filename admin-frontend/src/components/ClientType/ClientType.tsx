import { useTranslation } from 'react-i18next';

import * as schemas from '../../schemas';
import Tooltip from '../Tooltip/Tooltip';

interface ClientTypeProps {
  type: schemas.client.ClientType;
  tooltip?: boolean;
}

const ClientType: React.FunctionComponent<React.PropsWithChildren<ClientTypeProps>> = ({ type, tooltip }) => {
  const { t } = useTranslation('clients');

  return (
    <div className="flex">
      <span className="mr-1">{t(`clients:client_type.${type}`)}</span>
      {tooltip &&
        <Tooltip>
          {t(`clients:client_type_details.${type}`)}
        </Tooltip>
      }
    </div>
  );
};

export default ClientType;
