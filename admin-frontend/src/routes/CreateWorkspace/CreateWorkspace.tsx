import { Outlet } from 'react-router-dom';

import CreateWorkspaceContextProvider from '../../components/CreateWorkspaceContextProvider/CreateWorkspaceContextProvider';

const CreateWorkspace: React.FunctionComponent = () => {
  return (
    <CreateWorkspaceContextProvider>
      <Outlet />
    </CreateWorkspaceContextProvider>
  );
};

export default CreateWorkspace;
