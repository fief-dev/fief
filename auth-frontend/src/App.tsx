import React, { Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';

import './i18n';
import SignIn from './routes/SignIn/SignIn';

import './App.scss';

function App() {
  return (
    <Suspense fallback="loading">
      <Routes>
        <Route path="/login" element={<SignIn />} />
      </Routes>
    </Suspense>
  );
}

export default App;
