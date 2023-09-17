import './App.css';
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import GDriveConnector from './components/GDriveConnector'
import Main from './components/Main';
import Header from './components/Header';
import gdrive from './gdrive_logo.png'

function App() {
  return (
    <BrowserRouter>
    <Routes>
      <Route path="/" element={<GDriveConnector />} />
      <Route path="/main" element={<Main />} />
      {/* <Route path="/redirect" element={ <Navigate to="/main" /> }/> */}
    </Routes>
  </BrowserRouter>
   
  );
}

export default App;
