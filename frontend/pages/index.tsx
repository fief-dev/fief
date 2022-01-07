import type { GetServerSideProps, NextPage } from 'next';
import { serverSideTranslations } from 'next-i18next/serverSideTranslations';

import AuthLayout from '../components/AuthLayout/AuthLayout';
import SignIn from '../components/SignIn/SignIn';
import { useAPI } from '../hooks/api';
import { useTenantColors } from '../hooks/theme';

export const getServerSideProps: GetServerSideProps = async ({ locale }) => {
  return {
    props: {
      ...(await serverSideTranslations(locale as string, ['common', 'auth'])),
    },
  };
};

const Home: NextPage = () => {
  const api = useAPI('ACCOUNT');
  useTenantColors({});

  return (
    <AuthLayout title="Sign in" tenantName="Fief" tenantLogoURL="/fief-logo.svg">
      <SignIn api={api} />
    </AuthLayout>
  );
};

export default Home;
