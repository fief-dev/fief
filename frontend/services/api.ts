import axios, { AxiosError, AxiosInstance, AxiosResponse } from 'axios';
import * as R from 'ramda';

import * as schemas from '../schemas';

export class APIClient {
  client: AxiosInstance;

  constructor(accountId: string, tenantId?: string, domain?: string) {
    this.client = axios.create({
      baseURL: domain ? domain : process.env.NEXT_PUBLIC_BACKEND_HOST,
      withCredentials: true,
      headers: {
        'x-fief-account': accountId,
        ...tenantId ? { 'x-fief-tenant': tenantId } : {},
      },
    });
  }

  public login(data: schemas.auth.LoginData): Promise<AxiosResponse<void>> {
    return this.postFormData(
      '/auth/token/login',
      { username: data.email, password: data.password },
    );
  }

  private postFormData<T>(url: string, data: Record<string, any>): Promise<AxiosResponse<T>> {
    const formData = new FormData();
    Object.keys(data).forEach((key) => {
      const value = data[key];
      if (Array.isArray(value)) {
        for (const item of value) {
          formData.append(key, item);
        }
      } else {
        formData.set(key, data[key]);
      }
    });
    return this.client.post(url, formData, { headers: { 'Content-Type': 'multipart/form-data' }});
  }
}

const isAxiosException = (e: unknown): e is AxiosError<{ detail: string }> => R.has('isAxiosError', e);

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
