import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useSearchParams } from 'react-router-dom';

import AuthLayout from '../../components/AuthLayout/AuthLayout';
import ErrorAlert from '../../components/ErrorAlert/ErrorAlert';
import SignInForm from '../../components/SignInForm/SignInForm';
import { useAPI } from '../../hooks/api';
import { useAuthorizeResponse } from '../../hooks/authorize';

const SignIn: React.FunctionComponent = () => {
  const api = useAPI();
  const { t } = useTranslation(['common', 'auth']);
  const [searchParams] = useSearchParams();
  const [authorizeResponse, errorCode] = useAuthorizeResponse(api, searchParams);
  const tenant = useMemo(() => authorizeResponse ? authorizeResponse.tenant : undefined, [authorizeResponse]);

  return (
    <>
      <AuthLayout title={t('auth:signin.title')} tenant={tenant}>
        {!authorizeResponse && <ErrorAlert message={t(`common:api_errors.${errorCode}`)} />}
        {authorizeResponse && <SignInForm api={api} authorizationParameters={authorizeResponse?.parameters}/>}
      </AuthLayout>
    </>
  );
};

export default SignIn;
