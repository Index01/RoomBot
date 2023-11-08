import RoomSelekta from "./pages/RoomSelekta"
import Login from "./pages/Login"
import Admin from "./pages/Admin"
import Donate from "./pages/Donate"
import { Waittime, WaittimeList } from "./pages/Waittime"
import { Route, Routes , Navigate} from "react-router-dom"

export default function App() {
  document.body.style = "background: #343a40;";

  return (
    <Routes>
      <Route path="/bubbles" element={<Navigate to="/admin" replace />} />
      <Route path="/login" element={<Login />} />
      <Route path="/rooms" element={<RoomSelekta />} />
      <Route path="/admin" element={<Admin />} />
      <Route path="/donate" element={<Donate />} />
      <Route path="/waittime" element={<WaittimeList />} />
      <Route path="/waittime/:slug" element={<Waittime />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}
