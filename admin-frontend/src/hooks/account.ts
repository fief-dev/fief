import { createCache, useCache } from '@react-hook/cache';
import { Dispatch, useCallback, useEffect, useState } from 'react';

import { APIClient, isAxiosException } from '../services/api';
import * as schemas from '../schemas';

const accountsCache = createCache<schemas.account.AccountPublic[]>((async (key: string) => {
  const api = new APIClient();
  try {
    const { data } = await api.listAccounts();
    return data.results;
  } catch (err) {
    if (isAxiosException(err)) {
      const response = err.response;
      if (response && (response.status === 401 || response.status === 403)) {
        window.location.href = APIClient.getLoginURL();
      }
    }
  }
}) as (key: string) => Promise<schemas.account.AccountPublic[]>);

export const useAccountsCache = (): [schemas.account.AccountPublic[], boolean] => {
  const [{ status, value }, load] = useCache(accountsCache, 'accounts');
  const [accounts, setAccounts] = useState<schemas.account.AccountPublic[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (status === 'idle') {
      setLoading(true);
      load();
    }
  }, [status, load]);

  useEffect(() => {
    if (status === 'success' && value) {
      setAccounts(value);
      setLoading(false);
    }
  }, [status, value]);

  return [accounts, loading];
};

export const useCurrentAccount = (): [schemas.account.AccountPublic | undefined, Dispatch<schemas.account.AccountPublic>] => {
  const [accounts, loading] = useAccountsCache();
  const [account, setAccount] = useState<schemas.account.AccountPublic | undefined>();

  const getAccount = useCallback(async () => {
    const accountDomain = window.location.hostname;
    let account: schemas.account.AccountPublic | undefined;
    if (accountDomain) {
      account = accounts.find((account) => account.domain === accountDomain);
    }
    if (!account) {
      account = accounts[0];
    }
    return account;
  }, [accounts]);

  useEffect(() => {
    if (!loading && !account) {
      getAccount().then((account) => {
        setAccount(account);
      });
    }
  }, [getAccount, loading, account]);

  return [account, setAccount];
};
