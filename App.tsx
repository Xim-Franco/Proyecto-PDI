import React from 'react';
import './App.css';
import NavBarPr from "./Components/Navbar";
import 'bootstrap/dist/css/bootstrap.min.css';
import {router} from "./Routes/Routes";
import { RouterProvider } from 'react-router-dom';


function App() {
  return (
    <div className="App">
      <NavBarPr />
        <RouterProvider router={router} />
    </div>
  );
}

export default App;
