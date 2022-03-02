import React, { useState } from 'react';

import CreateAccountContext from '../../contexts/create-account';
import * as schemas from '../../schemas';

const CreateAccountContextProvider: React.FunctionComponent = ({ children }) => {
  const [createAccount, setCreateAccount] = useState<Partial<schemas.account.AccountCreate>>({});

  return (
    <CreateAccountContext.Provider value={[createAccount, setCreateAccount]}>
      {children}
    </CreateAccountContext.Provider>
  );
};

export default CreateAccountContextProvider;
