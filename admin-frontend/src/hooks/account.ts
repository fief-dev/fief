import { createCache, useCache } from '@react-hook/cache';
import { Dispatch, useCallback, useEffect, useState } from 'react';

import { APIClient, isAxiosException } from '../services/api';
import * as schemas from '../schemas';

const getAccountCookie = (): string | undefined => {
  const cookies = document.cookie.split(';');
  for (const cookie of cookies) {
    const [key, value] = cookie.trim().split('=');
    if (key === 'fief_account_id') {
      return value;
    }
  }
  return undefined;
}

const setAccountCookie = (value: string) => {
  document.cookie = `fief_account_id=${value}`;
};

const accountsCache = createCache<schemas.account.AccountPublic[]>((async (key: string) => {
  const api = new APIClient();
  try {
    const { data } = await api.listAccounts();
    return data.results;
  } catch (err) {
    if (isAxiosException(err)) {
      const response = err.response;
      if (response && (response.status === 401 || response.status === 403)) {
        window.location.href = api.getLoginURL();
      }
    }
  }
}) as (key: string) => Promise<schemas.account.AccountPublic[]>);

export const useAccountsCache = (): schemas.account.AccountPublic[] => {
  const [{ status, value }, load] = useCache(accountsCache, 'accounts');
  const [accounts, setAccounts] = useState<schemas.account.AccountPublic[]>([]);

  useEffect(() => {
    if (status === 'idle') {
      load();
    }
  }, [status, load]);

  useEffect(() => {
    if (status === 'success' && value) {
      setAccounts(value);
    }
  }, [status, value]);

  return accounts;
};

export const useCurrentAccount = (): [schemas.account.AccountPublic | undefined, Dispatch<schemas.account.AccountPublic>] => {
  const accounts = useAccountsCache();
  const [account, setAccount] = useState<schemas.account.AccountPublic | undefined>();

  const getAccount = useCallback(async () => {
    const accountId = getAccountCookie();
    let account: schemas.account.AccountPublic | undefined;
    if (accountId) {
      account = accounts.find((account) => account.id === accountId);
    }
    if (!account) {
      account = accounts[0];
    }
    return account;
  }, [accounts]);

  useEffect(() => {
    if (!account) {
      getAccount().then((account) => setAccount(account));
    }
  }, [getAccount, account]);

  useEffect(() => {
    if (account) {
      setAccountCookie(account.id);
    }
  }, [account]);

  return [account, setAccount];
};
