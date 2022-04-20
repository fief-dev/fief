import React from 'react';

import { APIClient } from '../services/api';

const APIClientContext = React.createContext<APIClient>(new APIClient());

export default APIClientContext;
