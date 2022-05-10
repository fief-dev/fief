import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import UserFieldsSelectionContext, { UserFieldSelection } from '../../contexts/user-fields-selection';
import { useUserFields } from '../../hooks/user-field';

const UserFieldsSelectionContextProvider: React.FunctionComponent = ({ children }) => {
  const { t } = useTranslation(['users']);
  const userFields = useUserFields();
  const [userFieldsSelection, setUserFieldsSelection] = useState<UserFieldSelection[]>([]);

  useEffect(() => {
    const userFieldsSelection: UserFieldSelection[] = [
      {
        id: 'id',
        name: t('users:list.id'),
        enabled: false,
      },
      {
        id: 'email',
        name: t('users:list.email'),
        enabled: true,
      },
      {
        id: 'tenant',
        name: t('users:list.tenant'),
        enabled: true,
      },
      ...userFields.map((userField) => ({
        id: userField.slug,
        name: userField.name,
        enabled: true,
      })),
    ];
    setUserFieldsSelection(userFieldsSelection);
  }, [userFields, t]);

  return (
    <UserFieldsSelectionContext.Provider value={[userFieldsSelection, setUserFieldsSelection]}>
      {children}
    </UserFieldsSelectionContext.Provider>
  );
};

export default UserFieldsSelectionContextProvider;
