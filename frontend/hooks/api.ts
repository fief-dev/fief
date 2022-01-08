import { useMemo } from 'react';

import { APIClient } from '../services/api';

export const useAPI = (tenantId?: string): APIClient => {
  return useMemo(() => new APIClient(tenantId), [tenantId]);
};
