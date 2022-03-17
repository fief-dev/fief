import React, { Dispatch } from 'react';

import * as schemas from '../schemas';

const CreateWorkspaceContext = React.createContext<[Partial<schemas.workspace.WorkspaceCreate>, Dispatch<Partial<schemas.workspace.WorkspaceCreate>>]>([{}, () => { }]);

export default CreateWorkspaceContext;
