import { Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';

import './i18n';
import UserContextProvider from './components/UserContextProvider/UserContextProvider';
import Dashboard from './routes/Dashboard/Dashboard';

function App() {
  return (
    <Suspense fallback="loading">
      <UserContextProvider>
        <Routes>
          <Route path="/" element={<Dashboard />} />
        </Routes>
      </UserContextProvider>
    </Suspense>
  );
}

export default App;
