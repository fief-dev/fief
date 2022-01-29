import { fireEvent, render, screen, waitFor } from '@testing-library/react';

import * as schemas from '../../schemas';
import { APIClient } from '../../services/api';
import SignIn from './SignInForm';

const mockLogin = jest.fn();
const mockAPIClient = { login: mockLogin } as unknown as APIClient;

const authorizationParameters: schemas.auth.AuthorizationParameters = {
  response_type: 'code',
  client_id: 'CLIENT_ID',
  redirect_uri: 'https://bretagne.duchy/callback',
  scope: null,
  state: null,
};

describe('SignIn', () => {
  beforeEach(() => {
    mockLogin.mockReset();
  });

  it('should validate that email and password are not empty', async () => {
    render(<SignIn api={mockAPIClient} authorizationParameters={authorizationParameters} />);

    const submitButton = screen.getByText('auth:signin.signin');
    fireEvent.click(submitButton);

    await waitFor(() =>
      expect(screen.getAllByText('common_errors.field_required')).toHaveLength(2)
    );

    const emailInput = screen.getByLabelText('auth:signin.email');
    expect(emailInput.classList).toContain('border-red-300');

    const passwordInput = screen.getByLabelText('auth:signin.password');
    expect(passwordInput.classList).toContain('border-red-300');
  });

  it('should show error code when API returns a 400 status code', async () => {
    mockLogin.mockRejectedValue({ isAxiosError: true, response: { status: 400, data: { detail: 'ERROR_CODE' } } });
    render(<SignIn api={mockAPIClient} authorizationParameters={authorizationParameters} />);

    const emailInput = screen.getByLabelText('auth:signin.email');
    fireEvent.change(emailInput, { target: { value: 'anne@bretagne.duchy' } });

    const passwordInput = screen.getByLabelText('auth:signin.password');
    fireEvent.change(passwordInput, { target: { value: 'hermine' } });

    const submitButton = screen.getByText('auth:signin.signin');
    fireEvent.click(submitButton);

    await waitFor(() =>
      expect(mockLogin).toHaveBeenCalledWith({ ...authorizationParameters, username: 'anne@bretagne.duchy', password: 'hermine' })
    );

    expect(screen.getByText('common:api_errors.ERROR_CODE')).toBeDefined();
  });

  it('should show unknown error code when API returns a non-400 error code', async () => {
    mockLogin.mockRejectedValue({ isAxiosError: true, response: { status: 502 } });
    render(<SignIn api={mockAPIClient} authorizationParameters={authorizationParameters} />);

    const emailInput = screen.getByLabelText('auth:signin.email');
    fireEvent.change(emailInput, { target: { value: 'anne@bretagne.duchy' } });

    const passwordInput = screen.getByLabelText('auth:signin.password');
    fireEvent.change(passwordInput, { target: { value: 'hermine' } });

    const submitButton = screen.getByText('auth:signin.signin');
    fireEvent.click(submitButton);

    await waitFor(() =>
      expect(mockLogin).toHaveBeenCalledWith({ ...authorizationParameters, username: 'anne@bretagne.duchy', password: 'hermine' })
    );

    expect(screen.getByText('common:api_errors.UNKNOWN_ERROR')).toBeDefined();
  });

  it('should hide error code on subsequent submissions', async () => {
    render(<SignIn api={mockAPIClient} authorizationParameters={authorizationParameters} />);

    const emailInput = screen.getByLabelText('auth:signin.email');
    fireEvent.change(emailInput, { target: { value: 'anne@bretagne.duchy' } });

    const passwordInput = screen.getByLabelText('auth:signin.password');
    fireEvent.change(passwordInput, { target: { value: 'hermine' } });

    const submitButton = screen.getByText('auth:signin.signin');

    mockLogin.mockRejectedValueOnce({ isAxiosError: true, response: { status: 502 } });
    fireEvent.click(submitButton);

    expect(await screen.findByText('common:api_errors.UNKNOWN_ERROR')).toBeDefined();

    mockLogin.mockResolvedValue({ status: 200, data: { redirect_uri: 'https://bretagne.duchy/callback' } });
    fireEvent.click(submitButton);

    await waitFor(() =>
      expect(screen.queryByText('common:api_errors.UNKNOWN_ERROR')).toBeNull()
    );
  });
});
