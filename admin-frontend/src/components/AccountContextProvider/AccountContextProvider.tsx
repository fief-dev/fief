import React from 'react';

import AccountContext from '../../contexts/account';
import { useCurrentAccount } from '../../hooks/account';

const AccountContextProvider: React.FunctionComponent = ({ children }) => {
  const [account, setCurrentAccount] = useCurrentAccount();

  return (
    <AccountContext.Provider value={[account, setCurrentAccount]}>
      {account && children}
    </AccountContext.Provider>
  );
};

export default AccountContextProvider;
