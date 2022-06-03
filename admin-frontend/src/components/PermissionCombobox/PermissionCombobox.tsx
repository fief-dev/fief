import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { useAPI } from '../../hooks/api';
import * as schemas from '../../schemas';
import ComboboxMultiple, { ComboboxMultipleOption } from '../ComboboxMultiple/ComboboxMultiple';

interface PermissionComboboxProps {
  value?: string[];
  onChange?: (value: string[]) => void;
  initialPermissions?: schemas.permission.Permission[];
}

const PermissionCombobox: React.FunctionComponent<React.PropsWithChildren<PermissionComboboxProps>> = ({ value, onChange, initialPermissions: _initialPermissions }) => {
  const { t } = useTranslation(['common']);
  const api = useAPI();

  const listPermissions = useCallback(async (query?: string): Promise<ComboboxMultipleOption[]> => {
    const { data: { results } } = await api.listPermissions({ ...(query ? { query } : {}) });
    return results.map((permission) => ({ value: permission.id, label: permission.codename }));
  }, [api]);

  const [initialPermissions, setInitialPermissions] = useState<ComboboxMultipleOption[]>(_initialPermissions ? _initialPermissions.map((permission) => ({ value: permission.id, label: permission.codename })) : []);
  useEffect(() => {
    if (initialPermissions.length === 0) {
      listPermissions().then((permissions) => {
        setInitialPermissions(permissions);
      });
    }
  }, [initialPermissions, listPermissions, value, onChange]);

  return (
    <ComboboxMultiple
      initialOptions={initialPermissions}
      onChange={onChange}
      value={value}
      noOptionLabel={t('permission_combobox.no_matching_permission')}
      onSearch={listPermissions}
    />
  )
};

export default PermissionCombobox;
