import { useCurrentUser } from '../../hooks/user';

const Dashboard: React.FunctionComponent = () => {
  const user = useCurrentUser();
  return (
    <>
      Hello {user.email}
    </>
  );
};

export default Dashboard;
