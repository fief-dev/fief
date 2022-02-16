import axios, { AxiosError, AxiosInstance, AxiosResponse } from 'axios';
import * as R from 'ramda';

import * as schemas from '../schemas';

export class APIClient {
  baseURL: string;
  client: AxiosInstance;

  constructor() {
    this.baseURL = process.env.REACT_APP_API_HOST as string;
    this.client = axios.create({
      baseURL: this.baseURL,
      withCredentials: true,
    });
  }

  public getLoginURL(): string {
    return this.baseURL + '/admin/auth/login';
  }

  public getUserinfo(): Promise<AxiosResponse<schemas.user.CurrentUser>> {
    return this.client.get('/admin/auth/userinfo');
  }

  public listAccounts(params: schemas.PaginationParameters = {}): Promise<AxiosResponse<schemas.PaginatedResults<schemas.account.AccountPublic>>> {
    return this.client.get('/admin/accounts/', { params });
  }

  public listTenants(params: schemas.PaginationParameters = {}): Promise<AxiosResponse<schemas.PaginatedResults<schemas.tenant.Tenant>>> {
    return this.client.get('/admin/tenants/', { params });
  }

  public listClients(params: schemas.PaginationParameters = {}): Promise<AxiosResponse<schemas.PaginatedResults<schemas.client.Client>>> {
    return this.client.get('/admin/clients/', { params });
  }

  public listUsers(params: schemas.PaginationParameters = {}): Promise<AxiosResponse<schemas.PaginatedResults<schemas.user.User>>> {
    return this.client.get('/admin/users/', { params });
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
