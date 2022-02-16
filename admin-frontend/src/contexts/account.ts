import React, { Dispatch } from 'react';

import * as schemas from '../schemas';

const AccountContext = React.createContext<[schemas.account.AccountPublic | undefined, Dispatch<schemas.account.AccountPublic>]>([undefined, () => { }]);

export default AccountContext;
