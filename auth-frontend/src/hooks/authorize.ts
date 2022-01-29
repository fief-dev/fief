import { useCallback, useEffect, useState } from 'react';

import * as schemas from '../schemas';
import { APIClient, handleAPIError } from '../services/api';

export const useAuthorizeResponse = (api: APIClient, searchParams: URLSearchParams): [schemas.auth.AuthorizeResponse | undefined, string | undefined] => {
  const [authorizeResponse, setAuthorizeResponse] = useState<schemas.auth.AuthorizeResponse | undefined>();
  const [errorCode, setErrorCode] = useState<string | undefined>();

  const getAuthorizeResponse = useCallback(async () => {
    try {
      const { data: _authorizeResponse } = await api.authorize(searchParams);
      setAuthorizeResponse(_authorizeResponse);
    } catch (err) {
      setErrorCode(handleAPIError(err));
    }
  }, [api, searchParams]);

  useEffect(() => {
    getAuthorizeResponse();
  }, [getAuthorizeResponse]);

  return [authorizeResponse, errorCode];
};
