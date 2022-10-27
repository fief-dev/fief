import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { useAPI } from '../../hooks/api';
import Combobox, { ComboboxOption } from '../Combobox/Combobox';

interface ClientComboboxProps {
  value?: string;
  onChange?: (value: string) => void;
}

const ClientCombobox: React.FunctionComponent<React.PropsWithChildren<ClientComboboxProps>> = ({ value, onChange }) => {
  const { t } = useTranslation(['common']);
  const api = useAPI();

  const listClients = useCallback(async (query?: string): Promise<ComboboxOption[]> => {
    const { data: { results } } = await api.listClients({ ...(query ? { query } : {}) });
    return results.map((client) => ({ value: client.id, label: client.name }));
  }, [api]);

  const [initialClients, setInitialClients] = useState<ComboboxOption[]>([]);
  useEffect(() => {
    if (initialClients.length === 0) {
      listClients().then((clients) => {
        setInitialClients(clients);
        if (!value && onChange) {
          onChange(clients[0].value);
        }
      });
    }
  }, [initialClients, listClients, value, onChange]);

  return (
    <Combobox
      initialOptions={initialClients}
      onChange={onChange}
      value={value}
      noOptionLabel={t('tenant_combobox.no_matching_tenant')}
      onSearch={listClients}
    />
  )
};

export default ClientCombobox;
