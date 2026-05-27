import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Home from './pages/Home.jsx';
import Horse from './pages/Horse.jsx';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/horse/:id" element={<Horse />} />
      </Routes>
    </BrowserRouter>
  );
}
