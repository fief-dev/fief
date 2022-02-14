import React from 'react';

import * as schemas from '../schemas';

const UserContext = React.createContext<schemas.user.CurrentUser | undefined>(undefined);

export default UserContext;
