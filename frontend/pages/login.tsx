import type { GetServerSideProps, NextPage } from 'next';
import { useTranslation } from 'next-i18next';
import { serverSideTranslations } from 'next-i18next/serverSideTranslations';

import AuthLayout from '../components/AuthLayout/AuthLayout';
import ErrorAlert from '../components/ErrorAlert/ErrorAlert';
import SignIn from '../components/SignIn/SignIn';
import { useAPI } from '../hooks/api';
import * as schemas from '../schemas';
import { APIClient, handleAPIError } from '../services/api';

interface LoginProps {
  tenant: schemas.tenant.TenantReadPublic | null;
  errorCode: string | null;
}

export const getServerSideProps: GetServerSideProps = async ({ locale, query, req, res }) => {
  const api = new APIClient(undefined, req);
  let tenant: schemas.tenant.TenantReadPublic | null = null;
  let errorCode: string | null = null;

  const client_id = query.client_id;

  if (client_id) {
    try {
      const { data } = await api.authorize(client_id as string);
      tenant = data;
    } catch (err) {
      res.statusCode = 400;
      errorCode = handleAPIError(err);
    }
  } else {
    res.statusCode = 400;
    errorCode = 'BAD_REQUEST';
  }

  return {
    props: {
      tenant,
      errorCode,
      ...(await serverSideTranslations(locale as string, ['common', 'auth'])),
    },
  };
};

const Login: NextPage<LoginProps> = ({ tenant, errorCode }) => {
  const api = useAPI();
  const { t } = useTranslation();

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
