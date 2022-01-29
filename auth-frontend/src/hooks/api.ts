import { useMemo } from 'react';

import { APIClient } from '../services/api';

export const useAPI = (): APIClient => {
  return useMemo(() => new APIClient(), []);
};
