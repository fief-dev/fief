import type { NextPage } from 'next';

import SignIn from '../components/SignIn/SignIn';
import { useAPI } from '../hooks/api';

const Home: NextPage = () => {
  const api = useAPI('ACCOUNT');

  return (
    <SignIn api={api} />
  );
};

export default Home;
