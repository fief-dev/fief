import { useMemo } from 'react';

import { APIClient } from '../services/api';

export const useAPI = (accountId: string, tenantId?: string, domain?: string): APIClient => {
  return useMemo(() => new APIClient(accountId, tenantId, domain), [accountId, tenantId, domain]);
};
