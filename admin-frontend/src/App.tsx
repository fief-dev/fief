import { Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';

import './i18n';
import UserContextProvider from './components/UserContextProvider/UserContextProvider';
import Dashboard from './routes/Dashboard/Dashboard';
import Clients from './routes/Clients/Clients';
import Tenants from './routes/Tenants/Tenants';
import Users from './routes/Users/Users';

function App() {
  return (
    <Suspense fallback="loading">
      <UserContextProvider>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/tenants" element={<Tenants />} />
          <Route path="/clients" element={<Clients />} />
          <Route path="/users" element={<Users />} />
        </Routes>
      </UserContextProvider>
    </Suspense>
  );
}

export default App;
