import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Home from './pages/Home.jsx';
import Horse from './pages/Horse.jsx';
import Farm from './pages/Farm.jsx';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/horse/:id" element={<Horse />} />
        <Route path="/farm/:name" element={<Farm />} />
      </Routes>
    </BrowserRouter>
  );
}
