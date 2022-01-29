import { useTranslation } from 'react-i18next';
import { useState } from 'react';
import { SubmitHandler, useForm } from 'react-hook-form';

import { useFieldRequiredErrorMessage } from '../../hooks/errors';
import * as schemas from '../../schemas';
import { APIClient, handleAPIError } from '../../services/api';
import ErrorAlert from '../ErrorAlert/ErrorAlert';
import FormErrorMessage from '../FormErrorMessage/FormErrorMessage';

interface SignInFormProps {
  api: APIClient;
  authorizationParameters: schemas.auth.AuthorizationParameters;
}

const SignInForm: React.FunctionComponent<SignInFormProps> = ({ api, authorizationParameters }) => {
  const { t } = useTranslation(['common', 'auth']);
  const { register, handleSubmit, formState: { errors } } = useForm<{ email: string, password: string }>();
  const fieldRequiredErrorMessage = useFieldRequiredErrorMessage();
  const [errorCode, setErrorCode] = useState<string | undefined>();

  const onSubmit: SubmitHandler<{ email: string, password: string }> = async ({ email, password }) => {
    setErrorCode(undefined);
    try {
      const { data: { redirect_uri }} = await api.login({ ...authorizationParameters, username: email, password });
      window.location.href = redirect_uri;
    } catch (err) {
      setErrorCode(handleAPIError(err));
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} action="/auth/login" method="POST">
      <div className="space-y-4">
        {errorCode && <ErrorAlert message={t(`common:api_errors.${errorCode}`)} />}
        <div>
          <label className="block text-sm font-medium mb-1" htmlFor="input-email">{t('auth:signin.email')}</label>
          <input
            id="input-email"
            className={`form-input w-full ${errors.email ? 'border-red-300' : ''}`}
            type="email"
            {...register('email', { required: fieldRequiredErrorMessage })}
          />
          <FormErrorMessage errors={errors} name="email" />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1" htmlFor="input-password">{t('auth:signin.password')}</label>
          <input
            id="input-password"
            className={`form-input w-full ${errors.email ? 'border-red-300' : ''}`}
            type="password"
            {...register('password', { required: fieldRequiredErrorMessage })}
          />
          <FormErrorMessage errors={errors} name="password" />
        </div>
      </div>
      <div className="flex items-center justify-between mt-6">
        <div className="mr-1">
          <a className="text-sm underline hover:no-underline" href="reset-password.html">Forgot Password?</a>
        </div>
        <button type="submit" className="btn bg-primary hover:bg-primary-hover text-white ml-3">{t('auth:signin.signin')}</button>
      </div>
    </form>
  );
};

export default SignInForm;
