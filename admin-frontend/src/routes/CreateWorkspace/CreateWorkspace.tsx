import { Outlet } from 'react-router-dom';

import CreateWorkspaceContextProvider from '../../components/CreateWorkspaceContextProvider/CreateWorkspaceContextProvider';

const CreateWorkspace: React.FunctionComponent<React.PropsWithChildren<unknown>> = () => {
  return (
    <CreateWorkspaceContextProvider>
      <Outlet />
    </CreateWorkspaceContextProvider>
  );
};

export default CreateWorkspace;
