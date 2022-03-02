import { Outlet } from 'react-router-dom';
import CreateAccountContextProvider from '../../components/CreateAccountContextProvider/CreateAccountContextProvider';

const CreateAccount: React.FunctionComponent = () => {
  return (
    <CreateAccountContextProvider>
      <Outlet />
    </CreateAccountContextProvider>
  );
};

export default CreateAccount;
