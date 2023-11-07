import "../styles/RoombotAdmin.css";
import HowLongTho from "../components/waittimes.js";
import React from "react";

const Waittime = () => {
  return(
    <div className="componentContainer">
      <div className="AppHeader">
	<img src="roombaht_header.png" alt="RoomBaht9000" />
      </div>
      <div className="DTApp">Wait Times
        <HowLongTho />
      </div>
    </div>
  );
};
export default Waittime
