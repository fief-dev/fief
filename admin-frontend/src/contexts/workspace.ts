import React, { Dispatch } from 'react';

import * as schemas from '../schemas';

const WorkspaceContext = React.createContext<[schemas.workspace.WorkspacePublic | undefined, Dispatch<schemas.workspace.WorkspacePublic>]>([undefined, () => { }]);

export default WorkspaceContext;
