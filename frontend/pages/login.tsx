import type { GetServerSideProps, NextPage } from 'next';
import { useTranslation } from 'next-i18next';
import { serverSideTranslations } from 'next-i18next/serverSideTranslations';
import { useMemo } from 'react';

import AuthLayout from '../components/AuthLayout/AuthLayout';
import ErrorAlert from '../components/ErrorAlert/ErrorAlert';
import SignIn from '../components/SignIn/SignIn';
import { useAPI } from '../hooks/api';
import * as schemas from '../schemas';
import { APIClient, handleAPIError } from '../services/api';

interface LoginProps {
  authorizeResponse: schemas.auth.AuthorizeResponse | null;
  errorCode: string | null;
}

export const getServerSideProps: GetServerSideProps = async ({ locale, query, req, res }) => {
  const api = new APIClient(undefined, req);
  let authorizeResponse: schemas.auth.AuthorizeResponse | null = null;
  let errorCode: string | null = null;

  try {
    const { data } = await api.authorize(query);
    authorizeResponse = data;
  } catch (err) {
    res.statusCode = 400;
    errorCode = handleAPIError(err);
  }

  return {
    props: {
      authorizeResponse,
      errorCode,
      ...(await serverSideTranslations(locale as string, ['common', 'auth'])),
    },
  };
};

const Login: NextPage<LoginProps> = ({ authorizeResponse, errorCode }) => {
  const api = useAPI();
  const { t } = useTranslation();
  const tenant = useMemo<schemas.tenant.TenantReadPublic | null>(
    () => authorizeResponse ? authorizeResponse.tenant : null,
    [authorizeResponse],
  );

  return (
    <>
      <AuthLayout title={t('auth:signin.title')} tenant={tenant}>
        {!tenant && <ErrorAlert message={t(`common:api_errors.${errorCode}`)} />}
        {tenant && <SignIn api={api} />}
      </AuthLayout>
    </>
  );
};

export default Login;
