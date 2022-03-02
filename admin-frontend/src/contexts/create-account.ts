import React, { Dispatch } from 'react';

import * as schemas from '../schemas';

const CreateAccountContext = React.createContext<[Partial<schemas.account.AccountCreate>, Dispatch<Partial<schemas.account.AccountCreate>>]>([{}, () => { }]);

export default CreateAccountContext;
