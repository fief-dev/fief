import axios, { AxiosError, AxiosInstance, AxiosResponse } from 'axios';
import { IncomingMessage } from 'http';
import * as R from 'ramda';

import * as schemas from '../schemas';

export class APIClient {
  client: AxiosInstance;

  constructor(tenantId?: string, req?: IncomingMessage) {
    this.client = axios.create({
      baseURL: req ? process.env.NEXT_PUBLIC_BACKEND_HOST : '/api',
      withCredentials: true,
      headers: {
        ...req ? { 'Host': req.headers.host } : {},
        ...tenantId ? { 'x-fief-tenant': tenantId } : {},
      },
    });
  }

  public authorize(params: any): Promise<AxiosResponse<schemas.auth.AuthorizeResponse>> {
    return this.client.get('/auth/authorize', { params });
  }

  public login(data: schemas.auth.LoginData): Promise<AxiosResponse<void>> {
    return this.postFormData(
      '/auth/login',
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
