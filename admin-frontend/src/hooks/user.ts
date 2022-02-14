import { useCallback, useContext } from 'react';

import UserContext from '../contexts/user';
import * as schemas from '../schemas';
import { isAxiosException } from '../services/api';
import { useAPI } from './api';

export const useGetCurrentUser = (): () => Promise<schemas.user.CurrentUser> => {
  const api = useAPI();

  const getCurrentUser = useCallback(async () => {
    try {
      const { data: userinfo } = await api.getUserinfo();
      return userinfo;
    } catch (err) {
      if (isAxiosException(err)) {
        const response = err.response;
        if (response && (response.status === 401 || response.status === 403)) {
          window.location.href = api.getLoginURL();
        }
      }
    }
  }, [api]) as () => Promise<schemas.user.CurrentUser>;

  return getCurrentUser;
};

export const useCurrentUser = (): schemas.user.CurrentUser => {
  return useContext(UserContext) as schemas.user.CurrentUser;
}
