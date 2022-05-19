import React, { useState } from 'react';

import CreateWorkspaceContext from '../../contexts/create-workspace';
import * as schemas from '../../schemas';

const CreateWorkspaceContextProvider: React.FunctionComponent<React.PropsWithChildren<unknown>> = ({ children }) => {
  const [createWorkspace, setCreateWorkspace] = useState<Partial<schemas.workspace.WorkspaceCreate>>({});

  return (
    <CreateWorkspaceContext.Provider value={[createWorkspace, setCreateWorkspace]}>
      {children}
    </CreateWorkspaceContext.Provider>
  );
};

export default CreateWorkspaceContextProvider;
