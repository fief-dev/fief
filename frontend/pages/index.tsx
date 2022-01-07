import type { GetServerSideProps, NextPage } from 'next';
import { serverSideTranslations } from 'next-i18next/serverSideTranslations';

import SignIn from '../components/SignIn/SignIn';
import { useAPI } from '../hooks/api';

export const getServerSideProps: GetServerSideProps = async ({ locale }) => {
  return {
    props: {
      ...(await serverSideTranslations(locale as string, ['common'])),
    },
  };
};

const Home: NextPage = () => {
  const api = useAPI('ACCOUNT');

  return (
    <SignIn api={api} />
  );
};

export default Home;
