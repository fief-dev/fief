import React from 'react';

export interface UserFieldSelection {
  id: string;
  name: string;
  enabled: boolean;
}

const UserFieldsSelectionContext = React.createContext<[UserFieldSelection[], React.Dispatch<React.SetStateAction<UserFieldSelection[]>>]>([[], () => { }]);

export default UserFieldsSelectionContext;
