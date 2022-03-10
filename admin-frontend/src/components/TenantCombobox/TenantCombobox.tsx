import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { useAPI } from '../../hooks/api';
import Combobox, { ComboboxOption } from '../Combobox/Combobox';

interface TenantComboboxProps {
  value?: string;
  onChange?: (value: string) => void;
}

const TenantCombobox: React.FunctionComponent<TenantComboboxProps> = ({ value, onChange }) => {
  const { t } = useTranslation(['common']);
  const api = useAPI();

  const listTenants = useCallback(async (query?: string): Promise<ComboboxOption[]> => {
    const { data: { results } } = await api.listTenants({ ...query ? { query } : {} });
    return results.map((tenant) => ({ value: tenant.id, label: tenant.name }));
  }, [api]);

  const [initialTenants, setInitialTenants] = useState<ComboboxOption[]>([]);
  useEffect(() => {
    if (initialTenants.length === 0) {
      listTenants().then((tenants) => {
        setInitialTenants(tenants);
        if (!value && onChange) {
          onChange(tenants[0].value);
        }
      });
    }
  }, [initialTenants, listTenants, value, onChange]);

  return (
    <Combobox
      initialOptions={initialTenants}
      onChange={onChange}
      value={value}
      noOptionLabel={t('tenant_combobox.no_matching_tenant')}
      onSearch={listTenants}
    />
  )
};

export default TenantCombobox;
