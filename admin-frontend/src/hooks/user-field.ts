import { useCallback, useEffect, useState } from 'react';

import * as schemas from '../schemas';
import { useAPI } from './api';

export const useUserFields = (): schemas.userField.UserField[] => {
  const api = useAPI();
  const [userFields, setUserFields] = useState<schemas.userField.UserField[]>([]);

  const getUserFields = useCallback(async () => {
    const { data } = await api.listUserFields({ limit: 100 });
    return data.results;
  }, [api]);

  useEffect(() => {
    getUserFields().then((userFields) => setUserFields(userFields));
  }, [getUserFields]);

  return userFields;
};
