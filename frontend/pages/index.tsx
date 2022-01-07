import type { GetServerSideProps, NextPage } from 'next';
import { serverSideTranslations } from 'next-i18next/serverSideTranslations';

import AuthLayout from '../components/AuthLayout/AuthLayout';
import SignIn from '../components/SignIn/SignIn';
import { useAPI } from '../hooks/api';

export const getServerSideProps: GetServerSideProps = async ({ locale }) => {
  return {
    props: {
      ...(await serverSideTranslations(locale as string, ['common', 'auth'])),
    },
  };
};

const Home: NextPage = () => {
  const api = useAPI('ACCOUNT');

  return (
    <AuthLayout title="Sign in">
      <SignIn api={api} />
    </AuthLayout>
  );
};

export default Home;
