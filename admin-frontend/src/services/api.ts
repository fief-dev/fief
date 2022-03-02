import axios, { AxiosError, AxiosInstance, AxiosResponse } from 'axios';
import * as R from 'ramda';

import * as schemas from '../schemas';

const API_PORT =  process.env.REACT_APP_API_PORT;
const BASE_URL = `${window.location.protocol}//${window.location.hostname}${API_PORT ? `:${API_PORT}` : ''}/api`;

export class APIClient {
  client: AxiosInstance;

  constructor(accountId?: string) {
    this.client = axios.create({
      baseURL: BASE_URL,
      withCredentials: true,
    });
  }

  public static getLoginURL(): string {
    return `${BASE_URL}/auth/login?redirect_uri=${encodeURIComponent(window.location.href)}`;
  }

  public getUserinfo(): Promise<AxiosResponse<schemas.user.CurrentUser>> {
    return this.client.get('/auth/userinfo');
  }

  public listAccounts(params: schemas.PaginationParameters = {}): Promise<AxiosResponse<schemas.PaginatedResults<schemas.account.AccountPublic>>> {
    return this.client.get('/accounts/', { params });
  }

  public createAccount(data: schemas.account.AccountCreate): Promise<AxiosResponse<schemas.account.AccountPublic>> {
    return this.client.post('/accounts/', data);
  }

  public listTenants(params: schemas.PaginationParameters = {}): Promise<AxiosResponse<schemas.PaginatedResults<schemas.tenant.Tenant>>> {
    return this.client.get('/tenants/', { params });
  }

  public listClients(params: schemas.PaginationParameters = {}): Promise<AxiosResponse<schemas.PaginatedResults<schemas.client.Client>>> {
    return this.client.get('/clients/', { params });
  }

  public listUsers(params: schemas.PaginationParameters = {}): Promise<AxiosResponse<schemas.PaginatedResults<schemas.user.User>>> {
    return this.client.get('/users/', { params });
  }
}

export const isAxiosException = (e: unknown): e is AxiosError<{ detail: string }> => R.has('isAxiosError', e);

export const handleAPIError = (err: unknown): string => {
  if (isAxiosException(err)) {
    const response = err.response;
    if (response && response.status === 400) {
      return response.data.detail;
    } else {
      return 'UNKNOWN_ERROR';
    }
  }
  throw err;
};
