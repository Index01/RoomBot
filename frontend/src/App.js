//import RoomDataTable from './components/dasDataTable.js';
//import "./styles/RoomDataTable.css";
import RoomSelekta from "./pages/RoomSelekta"
import Login from "./pages/Login"
import { Route, Routes } from "react-router-dom"



export default function App() {
  document.body.style = "background: #343a40;";

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/rooms" element={<RoomSelekta />} />
    </Routes>


    // <span className="componentContainer">

    //     <div className="AppHeader">
    //       <p>
    //          Select it. Swap it. Wtvr.
    //       </p>
    //     </div>
    //      
    //     <div className="DTApp">
    //       <RoomDataTable/>
    //     </div>
    // </span>
  );
}
