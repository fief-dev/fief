import axios, { AxiosError, AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import * as R from 'ramda';

import * as schemas from '../schemas';
import { LoginResponse } from '../schemas/auth';

export class APIClient {
  client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: process.env.REACT_APP_API_HOST,
      withCredentials: true,
    });
  }

  public authorize(params: any): Promise<AxiosResponse<schemas.auth.AuthorizeResponse>> {
    return this.client.get('/authorize', { params });
  }

  public async login(data: schemas.auth.LoginRequest): Promise<AxiosResponse<LoginResponse>> {
    return this.postFormData('/login', data);
  }

  private postFormData<T>(url: string, data: Record<string, any>, config?: AxiosRequestConfig<any>): Promise<AxiosResponse<T>> {
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
    return this.client.post(url, formData, { ...config, headers: { 'Content-Type': 'multipart/form-data' }});
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
