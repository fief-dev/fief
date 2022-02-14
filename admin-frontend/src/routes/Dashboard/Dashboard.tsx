import Layout from '../../components/Layout/Layout';
import { useCurrentUser } from '../../hooks/user';

const Dashboard: React.FunctionComponent = () => {
  const user = useCurrentUser();
  return (
    <Layout>
      Hello {user.email}
    </Layout>
  );
};

export default Dashboard;
