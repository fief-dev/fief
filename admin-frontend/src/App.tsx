import { Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';

import './i18n';
import UserContextProvider from './components/UserContextProvider/UserContextProvider';
import Dashboard from './routes/Dashboard/Dashboard';
import Tenants from './routes/Tenants/Tenants';

function App() {
  return (
    <Suspense fallback="loading">
      <UserContextProvider>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/tenants" element={<Tenants />} />
        </Routes>
      </UserContextProvider>
    </Suspense>
  );
}

export default App;
