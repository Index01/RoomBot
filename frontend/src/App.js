import RoomSelekta from "./pages/RoomSelekta"
import Login from "./pages/Login"
import Admin from "./pages/Admin"
import { Route, Routes , Navigate} from "react-router-dom"



export default function App() {
  document.body.style = "background: #343a40;";

  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<Login />} />
      <Route path="/rooms" element={<RoomSelekta />} />
      <Route path="/admin" element={<Admin />} />
    </Routes>

  );
}
