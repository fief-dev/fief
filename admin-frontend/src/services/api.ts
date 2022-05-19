import axios, { AxiosError, AxiosInstance, AxiosResponse } from 'axios';

import * as schemas from '../schemas';

export const API_PORT = process.env.REACT_APP_API_PORT || window.location.port;
export const FIEF_INSTANCE = `${window.location.protocol}//${window.location.hostname}${API_PORT ? `:${API_PORT}` : ''}`;
const BASE_URL = `${FIEF_INSTANCE}/admin/api`;

export class APIClient {
  client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: BASE_URL,
      withCredentials: true,
    });
  }

  public static getLoginURL(): string {
    return `${BASE_URL}/auth/login?redirect_uri=${encodeURIComponent(window.location.href)}`;
  }

  public static getLogoutURL(): string {
    return `${BASE_URL}/auth/logout`;
  }

  public getOpenAPI(): Promise<AxiosResponse<Record<string, any>>> {
    return this.client.get('/openapi.json');
  }

  public getUserinfo(): Promise<AxiosResponse<schemas.user.CurrentUser>> {
    return this.client.get('/auth/userinfo');
  }

  public listWorkspaces(params: schemas.PaginationParameters = {}): Promise<AxiosResponse<schemas.PaginatedResults<schemas.workspace.WorkspacePublic>>> {
    return this.client.get('/workspaces/', { params });
  }

  public createWorkspace(data: schemas.workspace.WorkspaceCreate): Promise<AxiosResponse<schemas.workspace.WorkspacePublic>> {
    return this.client.post('/workspaces/', data);
  }

  public checkConnectionWorkspace(data: schemas.workspace.WorkspaceCheckConnection): Promise<AxiosResponse<void>> {
    return this.client.post('/workspaces/check-connection', data);
  }

  public listTenants(params: schemas.tenant.TenantListParameters = {}): Promise<AxiosResponse<schemas.PaginatedResults<schemas.tenant.Tenant>>> {
    return this.client.get('/tenants/', { params });
  }

  public listClients(params: schemas.PaginationParameters = {}): Promise<AxiosResponse<schemas.PaginatedResults<schemas.client.Client>>> {
    return this.client.get('/clients/', { params });
  }

  public createClient(data: schemas.client.ClientCreate): Promise<AxiosResponse<schemas.client.Client>> {
    return this.client.post('/clients/', data);
  }

  public updateClient(id: string, data: schemas.client.ClientUpdate): Promise<AxiosResponse<schemas.client.Client>> {
    return this.client.patch(`/clients/${id}`, data);
  }

  public createClientEncryptionKey(id: string): Promise<AxiosResponse<Record<string, string>>> {
    return this.client.post(`/clients/${id}/encryption-key`);
  }

  public listUsers(params: schemas.PaginationParameters = {}): Promise<AxiosResponse<schemas.PaginatedResults<schemas.user.User>>> {
    return this.client.get('/users/', { params });
  }

  public createUser(data: schemas.user.UserCreateInternal): Promise<AxiosResponse<schemas.user.User>> {
    return this.client.post('/users/', data);
  }

  public updateUser(id: string, data: schemas.user.UserUpdate): Promise<AxiosResponse<schemas.user.User>> {
    return this.client.patch(`/users/${id}`, data);
  }

  public listUserFields(params: schemas.PaginationParameters = {}): Promise<AxiosResponse<schemas.PaginatedResults<schemas.userField.UserField>>> {
    return this.client.get('/user-fields/', { params });
  }

  public createUserField(data: schemas.userField.UserFieldCreate): Promise<AxiosResponse<schemas.userField.UserField>> {
    return this.client.post('/user-fields/', data);
  }

  public updateUserField(id: string, data: schemas.userField.UserFieldUpdate): Promise<AxiosResponse<schemas.userField.UserField>> {
    return this.client.patch(`/user-fields/${id}`, data);
  }

  public deleteUserField(id: string): Promise<AxiosResponse<void>> {
    return this.client.delete(`/user-fields/${id}`);
  }

  public listAPIKeys(params: schemas.PaginationParameters = {}): Promise<AxiosResponse<schemas.PaginatedResults<schemas.adminAPIKey.AdminAPIKey>>> {
    return this.client.get('/api-keys/', { params });
  }

  public createAPIKey(data: schemas.adminAPIKey.AdminAPIKeyCreate): Promise<AxiosResponse<schemas.adminAPIKey.AdminAPIKeyCreateResponse>> {
    return this.client.post('/api-keys/', data);
  }

  public deleteAPIKey(id: string): Promise<AxiosResponse<void>> {
    return this.client.delete(`/api-keys/${id}`);
  }
}

export const isAxiosException = (e: unknown): e is AxiosError<{ detail: any }> => e instanceof AxiosError;

interface FieldError {
  loc: string[];
  msg: string;
  type: string;
}

export const handleAPIError = (err: unknown): [string | undefined, FieldError[]] => {
  if (isAxiosException(err)) {
    const response = err.response;
    if (response) {
      if (response.status === 422) {
        return [undefined, response.data.detail];
      } else if (response.status === 400) {
        return [response.data.detail, []];
      } else {
        return ['UNKNOWN_ERROR', []];
      }
    }
  }
  throw err;
};
