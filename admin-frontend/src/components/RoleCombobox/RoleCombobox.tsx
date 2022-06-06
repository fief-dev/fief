import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { useAPI } from '../../hooks/api';
import * as schemas from '../../schemas';
import ComboboxMultiple, { ComboboxMultipleOption } from '../ComboboxMultiple/ComboboxMultiple';

interface RoleComboboxProps {
  value?: string[];
  onChange?: (value: string[]) => void;
  initialRoles?: schemas.role.Role[];
}

const RoleCombobox: React.FunctionComponent<React.PropsWithChildren<RoleComboboxProps>> = ({ value, onChange, initialRoles: _initialRoles }) => {
  const { t } = useTranslation(['common']);
  const api = useAPI();

  const listRoles = useCallback(async (query?: string): Promise<ComboboxMultipleOption[]> => {
    const { data: { results } } = await api.listRoles({ ...(query ? { query } : {}) });
    return results.map((role) => ({ value: role.id, label: role.name }));
  }, [api]);

  const [initialRoles, setInitialRoles] = useState<ComboboxMultipleOption[]>(_initialRoles ? _initialRoles.map((role) => ({ value: role.id, label: role.name })) : []);
  useEffect(() => {
    if (initialRoles.length === 0) {
      listRoles().then((roles) => {
        setInitialRoles(roles);
      });
    }
  }, [initialRoles, listRoles, value, onChange]);

  return (
    <ComboboxMultiple
      initialOptions={initialRoles}
      onChange={onChange}
      value={value}
      noOptionLabel={t('role_combobox.no_matching_role')}
      onSearch={listRoles}
    />
  )
};

export default RoleCombobox;
