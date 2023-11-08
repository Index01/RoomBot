import "../styles/RoombotAdmin.css";
import { TheTimers, HowLongTho } from "../components/waittimes.js";
import React from "react";
import { Toaster } from 'react-hot-toast';

export function Waittime() {
  return(
    <div className="componentContainer">
      <div className="AppHeader">
	<img src="/roombaht_header.png" alt="RoomBaht9000" />
      </div>
      <div className="DTApp">
        <HowLongTho />
      </div>
    </div>
  );
};

export function WaittimeList() {
  return(
    <>
    <div className="componentContainer">
      <div className="AppHeader">
	<img src="/roombaht_header.png" alt="RoomBaht9000" />
      </div>
      <div className="DTApp">Wait Times
        <TheTimers />
      </div>
    </div>
    <Toaster/>
    </>
  );
};
