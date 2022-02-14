import React, { useEffect, useState } from 'react';

import UserContext from '../../contexts/user';
import { useGetCurrentUser } from '../../hooks/user';
import * as schemas from '../../schemas';

const UserContextProvider: React.FunctionComponent = ({ children }) => {
  const getCurrentUser = useGetCurrentUser();
  const [currentUser, setCurrentUser] = useState<schemas.user.CurrentUser>();

  useEffect(() => {
    getCurrentUser().then((user) => setCurrentUser(user));
  }, [getCurrentUser]);

  return (
    <UserContext.Provider value={currentUser}>
      {currentUser && children}
    </UserContext.Provider>
  );
};

export default UserContextProvider;
